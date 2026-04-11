# backend/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
import json
import asyncio

from database import get_db
from models import ChatSession, ChatMessage, ChatFeedback, Vehicle
from services.chat_analysis import (
    build_query_plan, is_greeting, is_domain_query, has_known_vehicle_reference,
    is_location_query, is_list_query, is_compare_query, detect_explicit_vehicle,
    is_pronoun_query, needs_explicit_vehicle, should_use_grounded_fallback,
    detect_expertise
)
from services.retrieval import (
    search_vehicles, search_articles, build_context,
    retrieval_confidence, station_answer, summarize_inventory
)
from services.llm import generate_answer, fallback_answer

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class FeedbackRequest(BaseModel):
    session_id: str
    vehicle_id: int
    rating: int
    note: str | None = None

async def handle_initial_chat_logic(request: ChatRequest, db: Session):
    plan = build_query_plan(request.message, db)

    if request.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
    else:
        session = None
    
    if session is None:
        session = ChatSession(id=str(uuid.uuid4()), expertise_level="Novice")
        db.add(session)
        db.commit()

    # Expertise detection
    current_expertise = detect_expertise(request.message)
    if current_expertise != "Novice" and session.expertise_level == "Novice":
        session.expertise_level = current_expertise
    elif current_expertise == "Expert":
        session.expertise_level = "Expert"
    
    db.add(ChatMessage(session_id=session.id, role="user", content=request.message))
    db.commit()

    if is_greeting(request.message):
        return session.id, {
            "answer": "Hello! I hope you're having a great day. I'm your EViq assistant, ready to help you navigate the Indian EV market with ease. Whether you're looking for model comparisons, subsidy details, or technical charging advice, I'm here for you. How can I assist you in your EV journey today?",
            "sources": [],
        }, plan

    if not (is_domain_query(request.message) or has_known_vehicle_reference(request.message, db)):
        return session.id, {
            "answer": "I mainly help with India EV topics. Share your EV need (budget, segment, range, city, subsidy, comparison) and I will answer in detail.",
            "sources": [],
        }, plan

    if is_location_query(request.message):
        return session.id, {"answer": station_answer(request.message), "sources": []}, plan

    if plan.needs_clarification and plan.clarification_question:
        return session.id, {"answer": plan.clarification_question, "sources": []}, plan

    if is_list_query(request.message):
        return session.id, {"answer": summarize_inventory(db), "sources": []}, plan

    return session.id, None, plan

@router.post("/")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    session_id, initial_response, plan = asyncio.run(handle_initial_chat_logic(request, db))
    if initial_response:
        db.add(ChatMessage(session_id=session_id, role="assistant", content=initial_response["answer"]))
        db.commit()
        return {"success": True, "session_id": session_id, **initial_response}

    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

    # Retrieve relevant EVs
    explicit_id = detect_explicit_vehicle(request.message, db)
    vehicles = []
    if is_compare_query(request.message):
        vehicles = search_vehicles(request.message, db)
    elif explicit_id:
        v = db.query(Vehicle).filter(Vehicle.id == explicit_id).first()
        if v: vehicles = [v]
    elif is_pronoun_query(request.message) and session.last_vehicle_id:
        v = db.query(Vehicle).filter(Vehicle.id == session.last_vehicle_id).first()
        if v: vehicles = [v]
    elif needs_explicit_vehicle(request.message) and not session.last_vehicle_id:
        answer = "Please tell me the exact EV model name so I can give precise specs."
        return {"success": True, "session_id": session.id, "answer": answer, "sources": []}
    else:
        vehicles = search_vehicles(request.message, db)

    if vehicles:
        session.last_vehicle_id = vehicles[0].id
        db.commit()

    conf = retrieval_confidence(plan, vehicles, request.message)
    if is_pronoun_query(request.message) and session.last_vehicle_id and vehicles:
        conf = max(conf, 0.7)
    
    if conf < 0.45:
        answer = "I need one more detail for accurate results. Please share segment (2W/3W/4W/Truck/Bus) or budget and minimum range."
        return {"success": True, "session_id": session.id, "answer": answer, "sources": []}
    
    # RAG Context
    articles = search_articles(request.message, db)
    context = build_context(vehicles, articles)
    
    # Expertise tone adaptation
    tone = "simple and beginner-friendly"
    if session.expertise_level == "Enthusiast":
        tone = "knowledgeable and slightly technical"
    elif session.expertise_level == "Expert":
        tone = "highly technical, using industry terms (torque, NMC, BMS, TCO)"

    # Self-correction loop (feedback aware)
    corrections = ""
    past_feedback = db.query(ChatFeedback).filter(ChatFeedback.session_id == session.id, ChatFeedback.rating == -1).all()
    if past_feedback:
        corrections = "\nLessons from previous mistakes (Do NOT repeat these):\n"
        for fb in past_feedback:
            if fb.note: corrections += f"- {fb.note}\n"

    prompt = f"""You are an expert EV advisor for the Indian market.
Match the user's level: You are talking to a {session.expertise_level} so be {tone}.

Rules:
1) If the user asks about specific EV models, prices, ranges, or specifications, prioritize using the EV Database Context below.
2) If the specific EV data they asked for is missing from the context, clearly state 'That specific data is not available in my current dataset'.
3) For general EV knowledge, concepts, you can use your broader expert knowledge.
4) Keep answers concise.
5) comparisons should use markdown tables.
6) Always use Indian price formats.
{corrections}
EV Database Context:
{context}

User Question: {request.message}

Answer:"""

    if should_use_grounded_fallback(request.message):
        answer = fallback_answer(request.message, vehicles, articles)
    else:
        answer = generate_answer(prompt, request.message, vehicles, articles)

    db.add(ChatMessage(session_id=session.id, role="assistant", content=answer))
    db.commit()

    return {
        "success": True, "session_id": session.id, "answer": answer,
        "sources": [{"brand": v.brand, "model": v.model, "price": v.approx_price_inr, "range_km": v.range_km, "image_url": v.image_url} for v in vehicles]
    }

@router.post("/stream")
async def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    session_id, initial_response, plan = await handle_initial_chat_logic(request, db)

    if initial_response:
        db.add(ChatMessage(session_id=session_id, role="assistant", content=initial_response["answer"]))
        db.commit()
        async def stream_initial():
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
            yield f"data: {json.dumps({'type': 'chunk', 'content': initial_response['answer']})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'sources': []})}\n\n"
        return StreamingResponse(stream_initial(), media_type="text/event-stream")

    # (Simplified streaming logic similar to non-stream for brevity, but preserving core flow)
    vehicles = search_vehicles(request.message, db)
    articles = search_articles(request.message, db)
    context = build_context(vehicles, articles)
    
    prompt = f"EV Database Context: {context}\n\nUser Question: {request.message}"
    
    if should_use_grounded_fallback(request.message):
        answer = fallback_answer(request.message, vehicles)
    else:
        answer = generate_answer(prompt, request.message, vehicles)

    async def event_stream():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
        for token in answer.split(" "):
            yield f"data: {json.dumps({'type': 'chunk', 'content': token + ' '})}\n\n"
            await asyncio.sleep(0.01)
        yield f"data: {json.dumps({'type': 'done', 'sources': [{'brand': v.brand, 'model': v.model} for v in vehicles]})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.post("/feedback")
def feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    if request.rating not in (-1, 1):
        raise HTTPException(status_code=400, detail="rating must be 1 or -1")
    fb = ChatFeedback(session_id=request.session_id, vehicle_id=request.vehicle_id, rating=request.rating, note=request.note)
    db.add(fb)
    db.commit()
    return {"success": True}
