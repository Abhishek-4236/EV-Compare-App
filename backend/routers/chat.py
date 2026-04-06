# backend/routers/chat.py
from urllib import response

from urllib import response

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import Vehicle
from huggingface_hub import InferenceClient
import os

router = APIRouter(prefix="/api/chat", tags=["Chat"])

client = InferenceClient(
    model="microsoft/Phi-3-mini-4k-instruct",
    token=os.getenv("HF_TOKEN")
)

class ChatRequest(BaseModel):
    message: str

def search_vehicles(query: str, db: Session):
    """Retrieve relevant EVs from PostgreSQL based on keywords"""
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
    # Step 1: Retrieve relevant EVs
    vehicles = search_vehicles(request.message, db)
    
    # Step 2: Build context
    context = build_context(vehicles)
    
    # Step 3: Build prompt
    prompt = f"""You are an expert EV advisor for the Indian market. 
Answer the user's question using ONLY the provided EV data.
Be helpful, specific, and mention prices in Indian format (L for Lakhs).
If comparing, highlight key differences.

EV Database Context:
{context}

User Question: {request.message}

Answer:"""

    # Step 4: Call HuggingFace LLM
    try:
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Sorry, I couldn't process that. Error: {str(e)}"

    return {
        "success": True,
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