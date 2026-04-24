import re
from sqlalchemy import func
from sqlalchemy.orm import Session

from .embeddings import embed_text_if_ready
from models import ChatFeedback, KnowledgeArticle, Vehicle
from .chat_analysis import QueryPlan, infer_budget, normalize_query_text, tokenize


def retrieval_confidence(plan: QueryPlan, vehicles: list[Vehicle], query: str) -> float:
    if plan.intent in {"knowledge", "concept_compare", "location", "inventory", "greeting"}:
        return 1.0
    if not vehicles:
        return 0.0
    score = 0.25
    score += min(len(vehicles), 5) * 0.08
    if plan.segment:
        score += 0.15
    if plan.budget_max or plan.budget_min:
        score += 0.15
    if plan.min_range_km:
        score += 0.10
    q = (query or "").lower()
    if any(((vehicle.brand or "").lower() in q) or ((vehicle.model or "").lower() in q) for vehicle in vehicles):
        score += 0.15
    if plan.intent == "vehicle_compare" and len(vehicles) >= 2:
        score += 0.12
    if plan.intent == "spec" and len(vehicles) >= 1:
        score += 0.10
    return min(score, 1.0)


def search_vehicles(query: str, db: Session, plan: QueryPlan | None = None):
    # 0. Clean query for punctuation
    query_lower = normalize_query_text(query)
    query_lower = re.sub(r'[?.,!:]', '', query_lower)
    
    plan_intent = plan.intent if plan else None

    if plan_intent == "concept_compare":
        return []

    # Optimization: Filter via SQL ILIKE instead of fetching all into memory
    matched = db.query(Vehicle).filter(
        Vehicle.market_status == "Available",
        (
            func.lower(Vehicle.brand + " " + Vehicle.model).contains(query_lower) |
            func.lower(Vehicle.model).contains(query_lower) |
            func.lower(Vehicle.brand).contains(query_lower)
        )
    ).limit(10).all()

    candidates = db.query(Vehicle).filter(Vehicle.market_status == "Available").all()

    # Handle Brand-only matches if absolutely nothing found yet
    if not matched:
        for vehicle in candidates:
            brand_lower = (vehicle.brand or "").lower()
            if brand_lower and f" {brand_lower} " in f" {query_lower} " and len(brand_lower) >= 3:
                matched.append(vehicle)

    if plan_intent == "vehicle_compare" and len(matched) >= 2:
        return matched[:3]

    if plan_intent == "vehicle_compare":
        brand_hits = []
        for brand in [row[0] for row in db.query(Vehicle.brand).distinct().all()]:
            brand_lower = (brand or "").lower()
            if brand_lower and brand_lower in query_lower:
                brand_hits.append(brand)
        if len(brand_hits) >= 2:
            picked = []
            for brand in brand_hits[:3]:
                vehicle = (
                    db.query(Vehicle)
                    .filter(Vehicle.market_status == "Available", Vehicle.brand == brand)
                    .order_by(Vehicle.approx_price_inr.asc())
                    .first()
                )
                if vehicle:
                    picked.append(vehicle)
            if len(picked) >= 2:
                return picked

    if plan_intent == "spec" and matched:
        return matched[:1]

    db_query = db.query(Vehicle).filter(Vehicle.market_status == "Available")

    if any(word in query_lower for word in ["scooter", "scooty"]):
        db_query = db_query.filter(Vehicle.wheel_type.ilike("%scooter%"))
    elif any(word in query_lower for word in ["motorcycle", "bike"]):
        db_query = db_query.filter(Vehicle.wheel_type.ilike("%motorcycle%"))
    elif any(word in query_lower for word in ["car", "suv", "sedan", "hatchback", "family ev"]):
        db_query = db_query.filter(Vehicle.category == "4W")
    elif "truck" in query_lower:
        db_query = db_query.filter(Vehicle.category == "Truck")
    elif "bus" in query_lower:
        db_query = db_query.filter(Vehicle.category == "Bus")

    budget_min = plan.budget_min if plan and plan.budget_min else None
    budget_max = plan.budget_max if plan and plan.budget_max else None

    if not budget_min and not budget_max and not plan:
        budget_min, budget_max = infer_budget(query_lower)

    if budget_max:
        db_query = db_query.filter(Vehicle.approx_price_inr <= budget_max)
    if budget_min:
        db_query = db_query.filter(Vehicle.approx_price_inr >= budget_min)

    if plan and plan.min_range_km:
        db_query = db_query.filter(Vehicle.range_km >= plan.min_range_km)
    else:
        range_match = re.search(r"(\d+)\s*km", query_lower)
        if range_match:
            range_val = int(range_match.group(1))
            if range_val > 20:
                db_query = db_query.filter(Vehicle.range_km >= range_val)

    if plan and plan.segment:
        if plan.segment == "2W":
            db_query = db_query.filter(Vehicle.category == "2W")
        elif plan.segment == "3W":
            db_query = db_query.filter(Vehicle.category == "3W")
        elif plan.segment == "4W":
            db_query = db_query.filter(Vehicle.category == "4W")
        elif plan.segment == "4W_CAR":
            db_query = db_query.filter(
                Vehicle.category == "4W",
                Vehicle.vehicle_type.not_ilike("%commercial%"),
                Vehicle.vehicle_type.not_ilike("%cargo%"),
                Vehicle.vehicle_type.not_ilike("%truck%")
            )
        else:
            db_query = db_query.filter(Vehicle.category == plan.segment)

    exact_results = db_query.order_by(Vehicle.approx_price_inr.asc()).limit(10).all()
    if matched and plan_intent in {"recommend", "general", "subsidy"}:
        seen_ids = {vehicle.id for vehicle in matched}
        combined = matched + [vehicle for vehicle in exact_results if vehicle.id not in seen_ids]
        return combined[:5]

    if exact_results and plan_intent in {"recommend", "subsidy"}:
        return exact_results[:5]

    try:
        query_vec = embed_text_if_ready(query)
        if not query_vec:
            raise RuntimeError("Embedding model is still warming up")
        vector_query = db_query.filter(Vehicle.embedding.isnot(None))
        distance = Vehicle.embedding.cosine_distance(query_vec).label("distance")

        feedback_sum = (
            db.query(ChatFeedback.vehicle_id, func.coalesce(func.sum(ChatFeedback.rating), 0).label("fb"))
            .group_by(ChatFeedback.vehicle_id)
            .subquery()
        )

        boosted = (
            vector_query
            .outerjoin(feedback_sum, feedback_sum.c.vehicle_id == Vehicle.id)
            .add_columns(distance, func.coalesce(feedback_sum.c.fb, 0).label("fb"))
            .order_by(distance - (0.02 * func.coalesce(feedback_sum.c.fb, 0)))
        )

        rows = boosted.limit(25).all()
        q_tokens = set(tokenize(query_lower))
        scored = []
        for vehicle, dist, fb in rows:
            vehicle_text = f"{vehicle.brand} {vehicle.model} {vehicle.wheel_type or ''} {vehicle.category}".lower()
            vehicle_tokens = set(tokenize(vehicle_text))
            lexical = len(q_tokens.intersection(vehicle_tokens))
            semantic = 1 - float(dist or 1)
            feedback_boost = min(float(fb or 0) * 0.01, 0.05)
            score = (semantic * 0.7) + (lexical * 0.2) + feedback_boost
            if plan_intent == "recommend":
                score += 0.05
            scored.append((score, vehicle))
        scored.sort(key=lambda item: item[0], reverse=True)
        vehicles = [vehicle for _, vehicle in scored[:8]]
        if vehicles:
            return vehicles
    except Exception:
        pass

    if exact_results:
        return exact_results[:5]
    return db_query.order_by(Vehicle.approx_price_inr.asc()).limit(5).all()


CHAT_STATIONS = [
    {"name": "BESCOM EV Hub", "city": "Bengaluru"},
    {"name": "Ather Grid Koramangala", "city": "Bengaluru"},
    {"name": "Tata Power Pune Station", "city": "Pune"},
    {"name": "Jio-bp Charging Andheri", "city": "Mumbai"},
    {"name": "Delhi Public EV Point", "city": "Delhi"},
]


def station_answer(query: str) -> str:
    q = (query or "").lower()
    city_hits = [station for station in CHAT_STATIONS if station["city"].lower() in q]
    if not city_hits:
        city_match = next((city for city in ["bengaluru", "bangalore", "delhi", "mumbai", "pune", "hyderabad", "chennai"] if city in q), None)
        if city_match:
            pretty_city = "Bengaluru" if city_match == "bangalore" else city_match.title()
            return f"I do not have charging station entries for {pretty_city} in the current station dataset."
        return "I can help with charging locations if you share a city name that exists in the current station dataset."
    lines = [f"{station['name']} ({station['city']})" for station in city_hits]
    return "Here are useful charging locations: " + ", ".join(lines) + "."


def summarize_inventory(db: Session) -> str:
    total = db.query(Vehicle).count()
    by_cat = db.query(Vehicle.category, func.count(Vehicle.id)).group_by(Vehicle.category).all()
    cat_text = ", ".join([f"{category}: {count}" for category, count in by_cat])
    return f"We have {total} EVs in the database. Categories: {cat_text}. Tell me a segment (2W/3W/4W/Bus/Truck) and budget, and I will filter."


def search_articles(query: str, db: Session, limit: int = 3):
    try:
        query_vec = embed_text_if_ready(query)
        if not query_vec:
            raise RuntimeError("Embedding model is still warming up")
        return (
            db.query(KnowledgeArticle)
            .filter(KnowledgeArticle.embedding.isnot(None))
            .order_by(KnowledgeArticle.embedding.cosine_distance(query_vec))
            .limit(limit)
            .all()
        )
    except Exception:
        return []


def build_context(vehicles, articles=None):
    context_sections = []
    if vehicles:
        vehicle_context = "Here are relevant EVs from the India EV database:\n\n"
        for vehicle in vehicles:
            price_l = vehicle.approx_price_inr / 100000
            vehicle_context += f"- {vehicle.brand} {vehicle.model} ({vehicle.category} {vehicle.wheel_type}): "
            vehicle_context += f"₹{price_l:.1f}L, Range: {vehicle.range_km}km, "
            vehicle_context += f"Battery: {vehicle.battery_kwh}kWh, "
            vehicle_context += f"Top Speed: {vehicle.top_speed_kmh}kmph, "
            vehicle_context += f"Charging: {vehicle.charging_type}"
            if vehicle.fame2_subsidy_inr:
                vehicle_context += f", FAME II Subsidy: ₹{vehicle.fame2_subsidy_inr / 1000:.0f}K"
            if vehicle.overall_rating:
                vehicle_context += f", Rating: {vehicle.overall_rating}/5"
            if vehicle.extra_info:
                extra_str = ", ".join([f"{k}: {v}" for k, v in vehicle.extra_info.items()])
                vehicle_context += f", Extra Specs: {extra_str}"
            vehicle_context += "\n"
        context_sections.append(vehicle_context)

    if articles:
        article_context = "Here are relevant insights from EV Knowledge Articles:\n\n"
        for article in articles:
            article_context += f"--- Article: {article.title} ---\n{article.content}\n\n"
        context_sections.append(article_context)

    return "\n".join(context_sections) if context_sections else "No matching data found."
