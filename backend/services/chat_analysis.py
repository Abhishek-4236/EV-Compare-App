# backend/services/chat_analysis.py
import re
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import Vehicle

class QueryPlan(BaseModel):
    intent: str
    segment: str | None = None
    city: str | None = None
    budget_max: int | None = None
    min_range_km: int | None = None
    compare_targets: list[str] = []
    needs_clarification: bool = False
    clarification_question: str | None = None

DOMAIN_HINTS = [
    "ev", "electric", "vehicle", "car", "bike", "scooter", "motorcycle",
    "truck", "bus", "3w", "4w", "2w", "range", "battery", "charging",
    "subsidy", "fame", "price", "compare", "top speed", "station", "location",
    "feature", "spec", "model", "brand", "safety", "fire", "rain", "water",
    "myth", "fact", "life", "warranty", "maintenance", "cost", "tco",
    "torque", "nm", "kwh", "cells", "chemistry", "motor", "pmsm", "efficiency",
]

GREETING_HINTS = ["hi", "hello", "hey", "good morning", "good evening", "namaste", "yo"]

def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if len(t) >= 2]

def is_greeting(query: str) -> bool:
    q = (query or "").strip().lower()
    tokens = set(tokenize(q))
    phrase_greetings = [g for g in GREETING_HINTS if " " in g]
    single_greetings = {g for g in GREETING_HINTS if " " not in g}
    return any(p in q for p in phrase_greetings) or any(t in single_greetings for t in tokens)

def is_domain_query(query: str) -> bool:
    q = (query or "").lower()
    return any(token in q for token in DOMAIN_HINTS)

def has_known_vehicle_reference(query: str, db: Session) -> bool:
    q = (query or "").lower()
    if not q:
        return False
    rows = db.query(Vehicle.brand, Vehicle.model).all()
    for brand, model in rows:
        b = (brand or "").lower()
        m = (model or "").lower()
        if (b and b in q) or (m and len(m) >= 3 and m in q) or (b and m and f"{b} {m}" in q):
            return True
    return False

def is_location_query(query: str) -> bool:
    q = (query or "").lower()
    return any(token in q for token in ["station", "charging point", "charging location", "nearby", "location"])

def infer_budget(query_lower: str) -> int | None:
    # Look for patterns like "under 15L", "budget 10 lakh", or "₹1500000"
    # We exclude numbers immediately followed by 'km' to avoid range confusion
    if re.search(r'\d+\s*km', query_lower):
        query_lower = re.sub(r'\d+\s*km', '', query_lower)
    budget_match = re.search(r'(?:budget|under|around|price|₹)?\s*(\d+(?:\.\d+)?)\s*(k|l|lakh|lacs|cr)?', query_lower)
    if not budget_match:
        return None
    amount = float(budget_match.group(1))
    unit = budget_match.group(2) or ''
    if unit in ['l', 'lakh', 'lacs', 'lac']:
        amount *= 100000
    elif unit == 'cr':
        amount *= 10000000
    elif unit == 'k':
        amount *= 1000
    elif amount < 100 and not unit:
        # Likely referring to Lakhs if it's a small number without unit (e.g. "under 15")
        amount *= 100000
    return int(amount) if amount > 10000 else None

def infer_range_km(query_lower: str) -> int | None:
    m = re.search(r'(\d+)\s*km', query_lower)
    if not m:
        return None
    v = int(m.group(1))
    return v if v > 20 else None

def infer_segment(query_lower: str) -> str | None:
    if any(w in query_lower for w in ["scooter", "bike", "motorcycle", "2w"]):
        return "2W"
    if any(w in query_lower for w in ["rickshaw", "3w", "three wheeler"]):
        return "3W"
    if any(w in query_lower for w in ["car", "suv", "sedan", "hatchback", "4w"]):
        return "4W"
    if "truck" in query_lower:
        return "Truck"
    if "bus" in query_lower:
        return "Bus"
    return None

def infer_city(query_lower: str) -> str | None:
    for city in ["bengaluru", "bangalore", "delhi", "mumbai", "pune", "hyderabad", "chennai"]:
        if city in query_lower:
            return "bengaluru" if city == "bangalore" else city
    return None

def is_compare_query(query: str) -> bool:
    q = query.lower()
    # If the user is asking about theory concepts like AC vs DC, don't flag as vehicle comparison
    if "ac" in q and "dc" in q: return False
    if "charging" in q and "difference" in q: return False
    
    return any(
        phrase in q
        for phrase in ["compare", "vs", "versus", "difference", "differences"]
    )

def needs_explicit_vehicle(query: str) -> bool:
    q = query.lower()
    return any(
        phrase in q
        for phrase in [
            "battery", "top speed", "charging time", "key features",
            "features", "specs", "specifications", "warranty",
        ]
    )

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

def is_pronoun_query(query: str) -> bool:
    q = query.lower()
    return re.search(r"\b(it|its|this|that|this one|that one)\b", q) is not None

def is_list_query(query: str) -> bool:
    q = query.lower()
    return any(
        phrase in q
        for phrase in ["list all", "overall list", "all evs", "all vehicles", "entire list", "full list"]
    )

def should_use_grounded_fallback(query: str) -> bool:
    q = (query or "").lower()
    return (
        is_compare_query(q)
        or "subsidy" in q
        or "fame" in q
        or "top range" in q
        or "cheapest" in q
        or "under" in q
        or "best" in q
        or "recommend" in q
        or any(w in q for w in ["charging", "battery", "technology", "safety", "fire", "explain", "how", "what is"])
    )

def detect_expertise(query: str) -> str:
    q = query.lower()
    expert_terms = ["nm", "torque", "chemistry", "pmsm", "ah", "density", "tco", "lifecycle", "c-rating", "bms"]
    enthusiast_terms = ["kwh", "charging", "cc", "battery", "top speed", "kw", "efficiency", "ground clearance"]
    
    expert_hits = sum(1 for t in expert_terms if t in q)
    enthusiast_hits = sum(1 for t in enthusiast_terms if t in q)
    
    if expert_hits >= 2: return "Expert"
    if expert_hits >= 1 or enthusiast_hits >= 2: return "Enthusiast"
    return "Novice"

def build_query_plan(query: str, db: Session) -> QueryPlan:
    q = (query or "").lower().strip()
    plan = QueryPlan(intent="general")
    plan.budget_max = infer_budget(q)
    plan.min_range_km = infer_range_km(q)
    plan.segment = infer_segment(q)
    plan.city = infer_city(q)

    if is_compare_query(q):
        plan.intent = "compare"
    elif is_location_query(q):
        plan.intent = "location"
    elif any(token in q for token in ["safety", "fire", "rain", "water", "myth", "fact", "life", "warranty", "maintenance"]):
        plan.intent = "knowledge"
    elif "subsidy" in q or "fame" in q:
        plan.intent = "subsidy"
    elif any(token in q for token in ["battery", "nm", "torque", "lfp", "nmc", "chemistry"]):
        plan.intent = "knowledge"
    elif any(x in q for x in ["best", "recommend", "under", "budget", "top range", "longest range"]):
        plan.intent = "recommend"
    elif needs_explicit_vehicle(q) or has_known_vehicle_reference(q, db):
        plan.intent = "spec"

    # Detect brands OR models for comparison targets
    vehicles = db.query(Vehicle.brand, Vehicle.model).all()
    targets = set()
    for b, m in vehicles:
        if b.lower() in q: targets.add(b.lower())
        if m.lower() in q and len(m) > 3: targets.add(m.lower())
    plan.compare_targets = list(targets)[:3]

    if plan.intent == "compare" and len(plan.compare_targets) < 2 and not detect_explicit_vehicle(query, db):
        # If we didn't find specific cars, maybe it's just a general question about differences?
        # Let it slide to "knowledge" instead of blocking
        if any(w in q for w in ["charging", "battery", "technology", "subsidy"]):
            plan.intent = "knowledge"
            plan.needs_clarification = False
        else:
            plan.needs_clarification = True
            plan.clarification_question = "Please share two EV model or brand names to compare (e.g., Ola S1 Pro vs Ather 450X)."
    
    if plan.intent in {"recommend", "general"} and plan.segment is None and plan.budget_max is None and not has_known_vehicle_reference(query, db):
        # Allow general knowledge/technological queries to pass without preference clarification
        if not is_domain_query(q):
            plan.needs_clarification = True
            plan.clarification_question = "Tell me at least one preference: segment, budget, range, or city, and I will give accurate EV options."

    return plan
