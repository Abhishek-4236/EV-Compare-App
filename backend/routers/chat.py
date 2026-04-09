# backend/routers/chat.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import Vehicle, ChatSession, ChatMessage
from embeddings import embed_text
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError
import os
import uuid
import re

router = APIRouter(prefix="/api/chat", tags=["Chat"])

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL")
HF_PROVIDER = os.getenv("HF_PROVIDER", "auto")

client = InferenceClient(
    token=HF_TOKEN,
    provider=HF_PROVIDER
)

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


def is_pronoun_query(query: str) -> bool:
    q = query.lower()
    return re.search(r"\b(it|its|this|that|this one|that one)\b", q) is not None


def detect_explicit_vehicle(query: str, db: Session) -> int | None:
    q = query.lower()
    vehicles = db.query(Vehicle.id, Vehicle.brand, Vehicle.model).all()
    for v in vehicles:
        full = f"{v.brand} {v.model}".lower()
        if full in q:
            return v.id
    for v in vehicles:
        model = v.model.lower()
        if len(model) >= 4 and model in q:
            return v.id
    return None

def search_vehicles(query: str, db: Session):
    """Retrieve relevant EVs from PostgreSQL using vector similarity + optional filters"""
    query_lower = query.lower()
    
    # Determine category from query
    db_query = db.query(Vehicle).filter(Vehicle.market_status == "Available")
    
    if any(word in query_lower for word in ["scooter", "scooty"]):
        db_query = db_query.filter(Vehicle.wheel_type.ilike("%scooter%"))
    elif any(word in query_lower for word in ["motorcycle", "bike"]):
        db_query = db_query.filter(Vehicle.wheel_type.ilike("%motorcycle%"))
    elif any(word in query_lower for word in ["car", "suv", "sedan", "hatchback"]):
        db_query = db_query.filter(Vehicle.category == "4W")
    elif any(word in query_lower for word in ["truck"]):
        db_query = db_query.filter(Vehicle.category == "Truck")
    elif any(word in query_lower for word in ["bus"]):
        db_query = db_query.filter(Vehicle.category == "Bus")

    # Filter by budget if mentioned
    import re
    budget_match = re.search(r'₹?\s*(\d+)\s*(k|l|lakh|lacs|cr)?', query_lower)
    if budget_match:
        amount = int(budget_match.group(1))
        unit = budget_match.group(2) or ''
        if unit in ['l', 'lakh', 'lacs']:
            amount *= 100000
        elif unit == 'cr':
            amount *= 10000000
        elif unit == 'k':
            amount *= 1000
        elif amount < 1000:
            amount *= 100000  # assume lakhs
        if amount > 10000:
            db_query = db_query.filter(Vehicle.approx_price_inr <= amount)

    # Filter by range if mentioned
    range_match = re.search(r'(\d+)\s*km', query_lower)
    if range_match:
        range_val = int(range_match.group(1))
        if range_val > 20:
            db_query = db_query.filter(Vehicle.range_km >= range_val)

    # Vector similarity search
    try:
        query_vec = embed_text(query)
        db_query = db_query.filter(Vehicle.embedding.isnot(None))
        db_query = db_query.order_by(Vehicle.embedding.cosine_distance(query_vec))
        vehicles = db_query.limit(5).all()
        if vehicles:
            return vehicles
    except Exception:
        pass

    vehicles = db_query.order_by(Vehicle.overall_rating.desc()).limit(5).all()
    return vehicles


def build_context(vehicles):
    """Convert vehicle objects to readable text for LLM"""
    if not vehicles:
        return "No matching vehicles found in the database."
    
    context = "Here are relevant EVs from the India EV database:\n\n"
    for v in vehicles:
        price_l = v.approx_price_inr / 100000
        context += f"- {v.brand} {v.model} ({v.category} {v.wheel_type}): "
        context += f"₹{price_l:.1f}L, Range: {v.range_km}km, "
        context += f"Battery: {v.battery_kwh}kWh, "
        context += f"Top Speed: {v.top_speed_kmh}kmph, "
        context += f"Charging: {v.charging_type}"
        if v.fame2_subsidy_inr:
            context += f", FAME II Subsidy: ₹{v.fame2_subsidy_inr/1000:.0f}K"
        if v.overall_rating:
            context += f", Rating: {v.overall_rating}/5"
        context += "\n"
    return context


@router.post("/")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    # Step 0: Resolve session
    if request.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
    else:
        session = None

    if session is None:
        session = ChatSession(id=str(uuid.uuid4()))
        db.add(session)
        db.commit()

    # Store user message
    db.add(ChatMessage(session_id=session.id, role="user", content=request.message))
    db.commit()

    # Step 1: Retrieve relevant EVs
    explicit_id = detect_explicit_vehicle(request.message, db)
    vehicles = []

    if explicit_id:
        v = db.query(Vehicle).filter(Vehicle.id == explicit_id).first()
        if v:
            vehicles = [v]
            session.last_vehicle_id = v.id
            db.commit()
    elif is_pronoun_query(request.message) and session.last_vehicle_id:
        v = db.query(Vehicle).filter(Vehicle.id == session.last_vehicle_id).first()
        if v:
            vehicles = [v]
    else:
        vehicles = search_vehicles(request.message, db)
        if vehicles:
            session.last_vehicle_id = vehicles[0].id
            db.commit()
    
    # Step 2: Build context
    context = build_context(vehicles)
    
    # Step 3: Build prompt
    prompt = f"""You are an expert EV advisor for the Indian market. 
Answer the user's question using ONLY the provided EV data.
Be helpful, specific, and mention prices in Indian format (L for Lakhs).
If comparing, highlight key differences.
Be concise: 3-5 short sentences max.

EV Database Context:
{context}

User Question: {request.message}

Answer:"""

    # Step 4: Call HuggingFace LLM
    try:
        chat_kwargs = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
            "temperature": 0.7,
        }
        if HF_MODEL:
            chat_kwargs["model"] = HF_MODEL

        response = client.chat_completion(**chat_kwargs)
        answer = response.choices[0].message.content.strip()
    except HfHubHTTPError as e:
        err_msg = str(e)
        if "model_not_supported" in err_msg:
            answer = (
                "The selected Hugging Face model isn't available for your token/provider. "
                "Set HF_MODEL to a supported model, or enable an Inference Provider in your HF settings."
            )
        else:
            answer = f"Sorry, I couldn't process that. Error: {err_msg}"
    except Exception as e:
        answer = f"Sorry, I couldn't process that. Error: {str(e)}"

    # Store assistant message
    db.add(ChatMessage(session_id=session.id, role="assistant", content=answer))
    db.commit()

    return {
        "success": True,
        "session_id": session.id,
        "answer": answer,
        "sources": [
            {
                "brand": v.brand,
                "model": v.model,
                "price": v.approx_price_inr,
                "range_km": v.range_km
            } for v in vehicles
        ]
    }
