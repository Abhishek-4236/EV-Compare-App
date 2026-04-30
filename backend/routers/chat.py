import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import ChatFeedback, ChatMessage, ChatSession, Vehicle
from services.ev_rag import ev_rag_service
from services.llm import configured_provider_summary
from .auth import JWT_ALG, JWT_SECRET, read_bearer_token

router = APIRouter(prefix="/api/chat", tags=["Chat"])
_MEMORY_SESSIONS: dict[str, dict] = {}
_MEMORY_MESSAGES: dict[str, list[dict[str, str]]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class FeedbackRequest(BaseModel):
    session_id: str
    vehicle_id: int
    rating: int
    note: str | None = None


class SessionSaveRequest(BaseModel):
    title: str | None = None


def get_optional_user_id(authorization: str | None = Header(default=None)) -> int | None:
    if not authorization:
        return None
    token = read_bearer_token(authorization)
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except JWTError:
        return None


def get_owned_session_or_404(session_id: str, user_id: int | None, db: Session) -> ChatSession:
    if not user_id:
        raise HTTPException(status_code=401, detail="Sign in required")

    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


def get_or_create_session(request: ChatRequest, user_id: int | None, db: Session) -> ChatSession:
    title = request.message[:40] + ("..." if len(request.message) > 40 else "")
    fallback_id = request.session_id or str(uuid.uuid4())
    try:
        session = None
        if request.session_id:
            session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
        if session is None:
            session = ChatSession(id=str(uuid.uuid4()), expertise_level="Novice", user_id=user_id, title=title)
            db.add(session)
            db.commit()
        elif user_id and not session.user_id:
            session.user_id = user_id
            db.commit()
        return session
    except Exception:
        db.rollback()
        _MEMORY_SESSIONS.setdefault(
            fallback_id,
            {
                "id": fallback_id,
                "title": title,
                "created_at": datetime.now(UTC),
                "user_id": user_id,
            },
        )
        return ChatSession(
            id=fallback_id,
            expertise_level="Novice",
            user_id=user_id,
            title=title,
        )


def save_assistant_message(db: Session, session_id: str, answer: str) -> None:
    try:
        db.add(ChatMessage(session_id=session_id, role="assistant", content=answer))
        db.commit()
    except Exception:
        db.rollback()
        _MEMORY_MESSAGES.setdefault(session_id, []).append({"role": "assistant", "content": answer})


def build_history_context(db: Session, session_id: str) -> list[dict[str, str]]:
    try:
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(12)
            .all()
        )
        return [{"role": message.role, "content": message.content} for message in messages]
    except Exception:
        db.rollback()
        return _MEMORY_MESSAGES.get(session_id, [])[-12:]


def generate_chat_payload(request: ChatRequest, user_id: int | None, db: Session):
    if not (request.message or "").strip():
        return {
            "success": False,
            "session_id": request.session_id,
            "answer": "Please type an EV question and I’ll help.",
            "intent": "info",
            "parsed_query": None,
            "sources": [],
            "provider": None,
        }

    session = get_or_create_session(request, user_id, db)
    try:
        db.add(ChatMessage(session_id=session.id, role="user", content=request.message))
        db.commit()
    except Exception:
        db.rollback()
        _MEMORY_MESSAGES.setdefault(session.id, []).append({"role": "user", "content": request.message})

    history = build_history_context(db, session.id)
    normalized_message = request.message.strip().lower()
    if any(phrase in normalized_message for phrase in ["list all ev", "all evs", "show all vehicles", "show all evs", "full list"]):
        answer = ev_rag_service.inventory_summary()
        save_assistant_message(db, session.id, answer)
        return {
            "success": True,
            "session_id": session.id,
            "answer": answer,
            "intent": "info",
            "parsed_query": None,
            "sources": [],
            "provider": None,
        }
    try:
        result = ev_rag_service.answer(request.message, history)
    except FileNotFoundError:
        answer = (
            "The EV knowledge base is not built yet. "
            "Run `python scripts/build_ev_knowledge_base.py` inside `backend/` and try again."
        )
        save_assistant_message(db, session.id, answer)
        return {
            "success": False,
            "session_id": session.id,
            "answer": answer,
            "intent": "info",
            "parsed_query": None,
            "sources": [],
            "provider": None,
        }

    save_assistant_message(db, session.id, result.answer)
    source_payload = []
    vehicle_id_cache: dict[tuple[str, str, int | None, int | None], int | None] = {}
    for match in result.matches:
        key = (
            match.vehicle.brand,
            match.vehicle.model,
            match.vehicle.price_inr,
            match.vehicle.range_km,
        )
        if key not in vehicle_id_cache:
            vehicle_row = (
                db.query(Vehicle)
                .filter(
                    Vehicle.brand == match.vehicle.brand,
                    Vehicle.model == match.vehicle.model,
                )
                .first()
            )
            if vehicle_row is None and match.vehicle.price_inr is not None:
                vehicle_row = (
                    db.query(Vehicle)
                    .filter(
                        Vehicle.brand == match.vehicle.brand,
                        Vehicle.approx_price_inr == match.vehicle.price_inr,
                    )
                    .first()
                )
            vehicle_id_cache[key] = vehicle_row.id if vehicle_row else None

        source_payload.append(
            {
                "id": vehicle_id_cache[key],
                "vehicle_id": vehicle_id_cache[key],
                "rag_id": match.vehicle.id,
                "brand": match.vehicle.brand,
                "model": match.vehicle.model,
                "name": match.vehicle.name,
                "type": match.vehicle.vehicle_type,
                "price": match.vehicle.price_inr,
                "range_km": match.vehicle.range_km,
                "battery_kwh": match.vehicle.battery_kwh,
                "charging_time": match.vehicle.charging_time,
                "score": match.score,
            }
        )

    return {
        "success": True,
        "session_id": session.id,
        "answer": result.answer,
        "intent": result.intent,
        "parsed_query": result.parsed_query.model_dump(),
        "sources": source_payload,
        "provider": result.provider,
    }


@router.post("/")
def chat(request: ChatRequest, user_id: int | None = Depends(get_optional_user_id), db: Session = Depends(get_db)):
    return generate_chat_payload(request, user_id, db)


@router.post("/stream")
async def chat_stream(request: ChatRequest, user_id: int | None = Depends(get_optional_user_id), db: Session = Depends(get_db)):
    payload = generate_chat_payload(request, user_id, db)
    answer = payload["answer"]
    session_id = payload["session_id"]
    sources = payload.get("sources", [])
    provider = payload.get("provider")

    async def event_stream():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
        for token in answer.split(" "):
            yield f"data: {json.dumps({'type': 'chunk', 'content': token + ' '})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'sources': sources, 'provider': provider})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/feedback")
def feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    if request.rating not in (-1, 1):
        raise HTTPException(status_code=400, detail="rating must be 1 or -1")
    fb = ChatFeedback(session_id=request.session_id, vehicle_id=request.vehicle_id, rating=request.rating, note=request.note)
    try:
        db.add(fb)
        db.commit()
        return {"success": True}
    except Exception:
        db.rollback()
        return {"success": False}


@router.get("/sessions")
def get_user_sessions(user_id: int | None = Depends(get_optional_user_id), db: Session = Depends(get_db)):
    if not user_id:
        return []
    try:
        sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()).all()
        return [{"id": session.id, "title": session.title, "created_at": session.created_at} for session in sessions]
    except Exception:
        db.rollback()
        sessions = [
            session
            for session in _MEMORY_SESSIONS.values()
            if session.get("user_id") == user_id
        ]
        sessions.sort(key=lambda item: item.get("created_at") or datetime.now(UTC), reverse=True)
        return [{"id": session["id"], "title": session["title"], "created_at": session["created_at"]} for session in sessions]


@router.put("/sessions/{session_id}")
def save_session(
    session_id: str,
    request: SessionSaveRequest,
    user_id: int | None = Depends(get_optional_user_id),
    db: Session = Depends(get_db),
):
    session = get_owned_session_or_404(session_id, user_id, db)
    next_title = (request.title or session.title or "Saved chat").strip() or "Saved chat"
    session.title = next_title[:200]
    try:
        db.commit()
        db.refresh(session)
        return {"success": True, "id": session.id, "title": session.title, "created_at": session.created_at}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not save chat session")


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    user_id: int | None = Depends(get_optional_user_id),
    db: Session = Depends(get_db),
):
    session = get_owned_session_or_404(session_id, user_id, db)
    try:
        db.query(ChatFeedback).filter(ChatFeedback.session_id == session_id).delete(synchronize_session=False)
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete(synchronize_session=False)
        db.delete(session)
        db.commit()
        return {"success": True, "id": session_id}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not delete chat session")


@router.get("/history/{session_id}")
def get_session_history(session_id: str, db: Session = Depends(get_db)):
    try:
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
        return [{"role": message.role, "text": message.content} for message in messages]
    except Exception:
        db.rollback()
        return [{"role": message["role"], "text": message["content"]} for message in _MEMORY_MESSAGES.get(session_id, [])]


@router.get("/provider-status")
def provider_status():
    return configured_provider_summary()
