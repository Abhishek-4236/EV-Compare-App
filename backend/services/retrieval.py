# backend/services/retrieval.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Vehicle, KnowledgeArticle, ChatFeedback
from embeddings import embed_text
from .chat_analysis import tokenize, infer_budget, is_compare_query, QueryPlan
import re

def retrieval_confidence(plan: QueryPlan, vehicles: list[Vehicle], query: str) -> float:
    if not vehicles:
        return 0.0
    score = 0.25
    score += min(len(vehicles), 5) * 0.08
    if plan.segment:
        score += 0.15
    if plan.budget_max:
        score += 0.15
    if plan.min_range_km:
        score += 0.10
    q = (query or "").lower()
    if any(((v.brand or "").lower() in q) or ((v.model or "").lower() in q) for v in vehicles):
        score += 0.15
    if plan.intent == "compare" and len(vehicles) >= 2:
        score += 0.12
    return min(score, 1.0)

def search_vehicles(query: str, db: Session):
    """Retrieve relevant EVs using hybrid retrieval (keyword + vector)."""
    query_lower = query.lower()
    
    # Priority 1: Exact model name detection (Nexon, ZS EV, etc.)
    candidates = db.query(Vehicle).filter(Vehicle.market_status == "Available").all()
    matched = []
    for v in candidates:
        m = (v.model or "").lower()
        b = (v.brand or "").lower()
        # Direct model match or Brand + Model match
        if (m and m in query_lower) or (b and m and f"{b} {m}" in query_lower):
            matched.append(v)
    
    if len(matched) >= 2:
        return matched[:3]

    # Priority 2: Brand detection for comparisons (Legacy logic)
    if is_compare_query(query_lower):
        brands = [b[0] for b in db.query(Vehicle.brand).distinct().all()]
        brand_hits = []
        for b in brands:
            b_text = (b or "").lower()
            parts = [p for p in re.split(r"[^a-z0-9]+", b_text) if len(p) >= 3]
            if b_text in query_lower or any(p in query_lower for p in parts):
                brand_hits.append(b)
        
        if len(brand_hits) >= 2:
            picked = []
            for brand in brand_hits[:3]:
                # If we already have a matched vehicle for this brand, use it
                v_matched = next((m for m in matched if m.brand == brand), None)
                if v_matched:
                    picked.append(v_matched)
                else:
                    v = db.query(Vehicle).filter(Vehicle.market_status == "Available", Vehicle.brand == brand).order_by(Vehicle.overall_rating.desc()).first()
                    if v: picked.append(v)
            if len(picked) >= 2:
                return picked
    
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

    budget = infer_budget(query_lower)
    if budget:
        db_query = db_query.filter(Vehicle.approx_price_inr <= budget)

    range_match = re.search(r'(\d+)\s*km', query_lower)
    if range_match:
        range_val = int(range_match.group(1))
        if range_val > 20:
            db_query = db_query.filter(Vehicle.range_km >= range_val)

    try:
        query_vec = embed_text(query)
        db_query = db_query.filter(Vehicle.embedding.isnot(None))
        distance = Vehicle.embedding.cosine_distance(query_vec).label("distance")

        feedback_sum = (
            db.query(ChatFeedback.vehicle_id, func.coalesce(func.sum(ChatFeedback.rating), 0).label("fb"))
            .group_by(ChatFeedback.vehicle_id)
            .subquery()
        )

        boosted = (
            db_query
            .outerjoin(feedback_sum, feedback_sum.c.vehicle_id == Vehicle.id)
            .add_columns(distance, func.coalesce(feedback_sum.c.fb, 0).label("fb"))
            .order_by(distance - (0.02 * func.coalesce(feedback_sum.c.fb, 0)))
        )

        rows = boosted.limit(25).all()
        q_tokens = set(tokenize(query_lower))
        scored = []
        for vehicle, dist, fb in rows:
            v_text = f"{vehicle.brand} {vehicle.model} {vehicle.wheel_type or ''} {vehicle.category}".lower()
            v_tokens = set(tokenize(v_text))
            lexical = len(q_tokens.intersection(v_tokens))
            semantic = 1 - float(dist or 1)
            # Normalize feedback boost: max 0.05 to prevent it overriding relevance
            fb_boost = min(float(fb or 0) * 0.01, 0.05)
            score = (semantic * 0.7) + (lexical * 0.2) + fb_boost
            scored.append((score, vehicle))
        scored.sort(key=lambda x: x[0], reverse=True)
        vehicles = [v for _, v in scored[:5]]
        if vehicles:
            return vehicles
    except Exception:
        pass

    return db_query.order_by(Vehicle.overall_rating.desc()).limit(5).all()

CHAT_STATIONS = [
    {"name": "BESCOM EV Hub", "city": "Bengaluru"},
    {"name": "Ather Grid Koramangala", "city": "Bengaluru"},
    {"name": "Tata Power Pune Station", "city": "Pune"},
    {"name": "Jio-bp Charging Andheri", "city": "Mumbai"},
    {"name": "Delhi Public EV Point", "city": "Delhi"},
]

def station_answer(query: str) -> str:
    q = (query or "").lower()
    city_hits = [s for s in CHAT_STATIONS if s["city"].lower() in q]
    if not city_hits:
        city_hits = CHAT_STATIONS[:3]
    lines = [f"{s['name']} ({s['city']})" for s in city_hits]
    return "Here are useful charging locations: " + ", ".join(lines) + "."

def summarize_inventory(db: Session) -> str:
    total = db.query(Vehicle).count()
    by_cat = db.query(Vehicle.category, func.count(Vehicle.id)).group_by(Vehicle.category).all()
    cat_text = ", ".join([f"{c}: {n}" for c, n in by_cat])
    return f"We have {total} EVs in the database. Categories: {cat_text}. Tell me a segment (2W/3W/4W/Bus/Truck) and budget, and I will filter."

def search_articles(query: str, db: Session, limit: int = 3):
    try:
        query_vec = embed_text(query)
        articles = (
            db.query(KnowledgeArticle)
            .filter(KnowledgeArticle.embedding.isnot(None))
            .order_by(KnowledgeArticle.embedding.cosine_distance(query_vec))
            .limit(limit)
            .all()
        )
        return articles
    except Exception:
        return []

def build_context(vehicles, articles=None):
    context_sections = []
    if vehicles:
        v_context = "Here are relevant EVs from the India EV database:\n\n"
        for v in vehicles:
            price_l = v.approx_price_inr / 100000
            v_context += f"- {v.brand} {v.model} ({v.category} {v.wheel_type}): "
            v_context += f"\u20b9{price_l:.1f}L, Range: {v.range_km}km, "
            v_context += f"Battery: {v.battery_kwh}kWh, "
            v_context += f"Top Speed: {v.top_speed_kmh}kmph, "
            v_context += f"Charging: {v.charging_type}"
            if v.fame2_subsidy_inr:
                v_context += f", FAME II Subsidy: \u20b9{v.fame2_subsidy_inr/1000:.0f}K"
            if v.overall_rating:
                v_context += f", Rating: {v.overall_rating}/5"
            v_context += "\n"
        context_sections.append(v_context)
        
    if articles:
        a_context = "Here are relevant insights from EV Knowledge Articles:\n\n"
        for a in articles:
            a_context += f"--- Article: {a.title} ---\n{a.content}\n\n"
        context_sections.append(a_context)
        
    return "\n".join(context_sections) if context_sections else "No matching data found."
