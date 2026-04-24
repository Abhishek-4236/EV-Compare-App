import re
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from models import Vehicle


class QueryPlan(BaseModel):
    intent: str
    segment: str | None = None
    city: str | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    min_range_km: int | None = None
    compare_targets: list[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: str | None = None


DOMAIN_HINTS = [
    "ev", "evs", "electric", "vehicle", "vehicles", "car", "cars", "bike", "scooter",
    "motorcycle", "truck", "bus", "battery", "charging", "charger", "range", "kms",
    "kilometer", "price", "subsidy", "fame", "pm e-drive", "running cost", "tco",
    "regen", "regenerative", "braking", "bms", "cell balancing", "lfp", "nmc",
    "battery life", "fast charging", "slow charging", "ac", "dc", "motor", "torque",
    "chemistry", "kwh", "thermal", "safety", "warranty", "maintenance", "top speed", "specs", "spec",
    "station",
    "charging station", "connector", "ground clearance", "student commute", "college",
    "petrol", "diesel", "hybrid", "family ev", "best ev", "best scooter",
]

KNOWLEDGE_HINTS = [
    "regen", "regenerative", "bms", "cell", "balancing", "lfp", "nmc", "chemistry",
    "battery life", "fast charging", "slow charging", "thermal", "motor", "torque",
    "charging curve", "fire", "rain", "water", "maintenance", "warranty", "myth",
    "fact", "ac charging", "dc charging", "running cost", "petrol", "diesel",
]

GREETING_HINTS = [
    "hi", "hello", "hey", "good morning", "good evening", "namaste", "yo",
    "hie", "heyy", "heyyy", "hellooo", "helloooo", "sup", "whats up", "what's up",
]

CONCEPT_COMPARE_KEYWORDS = [
    "ac", "dc", "lfp", "nmc", "petrol", "diesel", "battery", "batteries", "charging",
    "charger", "chemistry", "motor", "motors", "cell", "cells", "thermal",
]

BRAND_ALIASES = {
    "tata": ["tata motors", "tata"],
    "ola": ["ola electric", "ola"],
    "mahindra": ["mahindra & mahindra", "mahindra electric", "mahindra"],
    "m&m": ["mahindra"],
    "ather": ["ather energy", "ather"],
    "mg": ["mg motor", "mg motors", "mg"],
    "hyundai": ["hyundai motors", "hyundai"],
    "kia": ["kia motors", "kia"],
    "byd": ["byd india", "byd"],
    "herohonda": ["hero"],
    "hero": ["hero moto corp", "hero electric", "hero vida", "hero"],
    "vida": ["hero vida", "vida"],
    "tvs": ["tvs motors", "tvs"],
    "bajaj": ["bajaj auto", "bajaj"],
}

QUERY_NORMALIZATIONS = {
    "ev's": "evs",
    "electic": "electric",
    "electrik": "electric",
    "vehical": "vehicle",
    "vehicals": "vehicles",
    "battary": "battery",
    "batterry": "battery",
    "charing": "charging",
    "chargin": "charging",
    "chargng": "charging",
    "scooty": "scooter",
    "milage": "range",
    "mileage": "range",
    "pickup": "acceleration",
    "costing": "price",
    "specification": "spec",
    "specifications": "specs",
}


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if len(t) >= 1]


def normalize_query_text(text: str) -> str:
    q = (text or "").lower().strip()
    q = re.sub(r"[^\w\s₹.-]", " ", q)
    for wrong, right in QUERY_NORMALIZATIONS.items():
        q = re.sub(rf"\b{re.escape(wrong)}\b", right, q)
    q = re.sub(r"\b(?:pls|pls\.|plz)\b", "please", q)
    q = re.sub(r"\b(?:wanna|wantta)\b", "want", q)
    q = re.sub(r"\b(?:which\s+ev\s+should\s+i\s+buy)\b", "best ev to buy", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q


def normalized_text(text: str) -> str:
    return " ".join(tokenize(normalize_query_text(text)))


def is_greeting(query: str) -> bool:
    q = normalize_query_text(query)
    if not q:
        return False
    q_norm = normalized_text(q)
    tokens = set(tokenize(q))
    phrase_greetings = {phrase for phrase in GREETING_HINTS if " " in phrase}
    single_greetings = {phrase for phrase in GREETING_HINTS if " " not in phrase}
    if q_norm in phrase_greetings:
        return True
    if tokens and tokens.issubset(single_greetings):
        return True
    return re.fullmatch(r"(h+i+|h+e+y+|h+e+l+o+|h+i+e+|y+o+)", q) is not None


def is_domain_query(query: str) -> bool:
    q = normalize_query_text(query)
    tokens = set(tokenize(q))
    return any(hint in q for hint in DOMAIN_HINTS) or bool(tokens.intersection({"ev", "evs", "battery", "charging", "range"}))


def _fallback_vehicle_name_rows() -> list[tuple[str, str]]:
    try:
        from services.ev_rag import ev_rag_service

        return [
            (vehicle.brand, vehicle.model)
            for vehicle in ev_rag_service.artifacts.vehicles
        ]
    except Exception:
        return []


def _vehicle_name_rows(db: Session | None) -> list[tuple[str, str]]:
    if db is not None:
        try:
            return db.query(Vehicle.brand, Vehicle.model).all()
        except Exception:
            pass
    return _fallback_vehicle_name_rows()


def has_known_vehicle_reference(query: str, db: Session) -> bool:
    q = normalize_query_text(query)
    if not q:
        return False
    rows = _vehicle_name_rows(db)
    for brand, model in rows:
        brand_lower = (brand or "").lower()
        model_lower = (model or "").lower()
        # Direct check
        if (brand_lower and brand_lower in q) or (model_lower and len(model_lower) >= 3 and model_lower in q):
            return True
        # Partial model match (e.g. 'S1 X' matching 'S1 X 2kWh')
        if model_lower and len(model_lower) > 3:
            for part in q.split():
                if len(part) >= 3 and part in model_lower:
                    return True
    return False


def is_location_query(query: str) -> bool:
    q = normalize_query_text(query)
    return any(token in q for token in ["station", "charging point", "charging location", "nearby", "location", "charger near"])


def infer_budget(query_lower: str) -> tuple[int | None, int | None]:
    if re.search(r"\d+\s*km", query_lower):
        query_lower = re.sub(r"\d+\s*km", "", query_lower)
        
    def scale(amt, u):
        if u in ["l", "lakh", "lacs", "lac"]: return amt * 100000
        if u == "cr": return amt * 10000000
        if u == "k": return amt * 1000
        if amt < 100 and not u: return amt * 100000
        return amt

    range_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to|and)\s*(\d+(?:\.\d+)?)\s*(k|l|lakh|lacs|lac|cr)?", query_lower)
    if range_match:
        min_amt = float(range_match.group(1))
        max_amt = float(range_match.group(2))
        unit = range_match.group(3) or ""
        return int(scale(min_amt, unit)), int(scale(max_amt, unit))

    budget_match = re.search(r"(?:budget|under|around|price|₹)?\s*(\d+(?:\.\d+)?)\s*(k|l|lakh|lacs|lac|cr)?", query_lower)
    if not budget_match:
        return None, None
    amount = float(budget_match.group(1))
    unit = budget_match.group(2) or ""
    final_amt = int(scale(amount, unit))
    if final_amt > 10000:
        return None, final_amt
    return None, None


def infer_range_km(query_lower: str) -> int | None:
    match = re.search(r"(\d+)\s*km", query_lower)
    if not match:
        return None
    value = int(match.group(1))
    return value if value > 20 else None


def infer_segment(query_lower: str) -> str | None:
    if any(word in query_lower for word in ["scooter", "bike", "motorcycle", "2w", "two wheeler"]):
        return "2W"
    if any(word in query_lower for word in ["rickshaw", "3w", "three wheeler"]):
        return "3W"
    if any(word in query_lower for word in ["car", "suv", "sedan", "hatchback", "family ev"]):
        return "4W_CAR"
    if "4w" in query_lower:
        return "4W"
    if "truck" in query_lower:
        return "Truck"
    if "bus" in query_lower:
        return "Bus"
    return None


def infer_city(query_lower: str) -> str | None:
    for city in ["bengaluru", "bangalore", "delhi", "mumbai", "pune", "hyderabad", "chennai", "kerala"]:
        if city in query_lower:
            return "bengaluru" if city == "bangalore" else city
    return None


def _has_compare_marker(query: str) -> bool:
    q = normalize_query_text(query)
    tokens = tokenize(q)
    token_set = set(tokens)
    return (
        "compare" in token_set
        or "versus" in token_set
        or "vs" in token_set
        or "difference" in token_set
        or "differences" in token_set
        or "better" in token_set
        or ("between" in token_set and len(token_set.intersection({"and", "or"})) > 0)
    )


def is_concept_compare_query(query: str, db: Session | None = None) -> bool:
    q = normalize_query_text(query)
    tokens = set(tokenize(q))
    if not _has_compare_marker(q):
        return False
    if db is not None and len(extract_compare_targets(query, db)) >= 2:
        if not ({"ac", "dc"}.issubset(tokens) or {"lfp", "nmc"}.issubset(tokens) or ("petrol" in tokens and "ev" in tokens) or ("diesel" in tokens and "ev" in tokens)):
            return False
    if {"ac", "dc"}.issubset(tokens):
        return True
    if {"lfp", "nmc"}.issubset(tokens):
        return True
    if "petrol" in tokens and "ev" in tokens:
        return True
    if "diesel" in tokens and "ev" in tokens:
        return True
    return any(keyword in q for keyword in ["battery", "batteries", "charging", "chemistry", "running cost"])


def is_vehicle_compare_query(query: str, db: Session | None = None) -> bool:
    q = normalize_query_text(query)
    if not _has_compare_marker(q):
        return False
    if is_concept_compare_query(query, db):
        return False
    if db is None:
        return True
    return has_known_vehicle_reference(query, db)


def is_compare_query(query: str) -> bool:
    return _has_compare_marker(query)


def needs_explicit_vehicle(query: str) -> bool:
    q = normalize_query_text(query)
    return any(
        phrase in q
        for phrase in [
            "battery", "top speed", "charging time", "key features",
            "features", "specs", "specifications", "warranty",
            "price and battery", "dc fast charging",
        ]
    )


def detect_explicit_vehicle(query: str, db: Session) -> int | None:
    # 0. Clean the query
    q = normalize_query_text(query)
    q = re.sub(r'[?.,!:]', '', q) # Remove common sentence-enders
    try:
        vehicles = db.query(Vehicle.id, Vehicle.brand, Vehicle.model).all()
    except Exception:
        vehicles = [
            (idx + 1, brand, model)
            for idx, (brand, model) in enumerate(_vehicle_name_rows(db))
        ]
    
    # 1. Exact full match (Brand + Model)
    for vehicle in vehicles:
        vehicle_id, brand, model = vehicle
        full = f"{brand} {model}".lower()
        if full in q: return vehicle_id
    
    # 2. Check Aliases + Model
    for vehicle in vehicles:
        vehicle_id, brand, model = vehicle
        brand_lower = (brand or "").lower()
        model_lower = (model or "").lower()
        
        # Check if query contains any alias for this vehicle's brand
        matched_brand = False
        for alias, targets in BRAND_ALIASES.items():
            if alias in q and any(t in brand_lower for t in targets):
                matched_brand = True
                break
        
        if matched_brand:
            model_parts = [p for p in model_lower.split() if len(p) >= 2]
            if model_parts and all(f" {p} " in f" {q} " for p in model_parts):
                return vehicle_id
            if model_parts and f" {model_parts[0]} " in f" {q} " and len(model_parts[0]) >= 3:
                return vehicle_id

    # 3. Model alone (Unique and > 3 chars)
    for vehicle in vehicles:
        vehicle_id, _, model = vehicle
        model_lower = model.lower()
        if len(model_lower) >= 4 and f" {model_lower} " in f" {q} ":
            return vehicle_id
            
    return None


def extract_compare_targets(query: str, db: Session) -> list[str]:
    # 0. Clean the query
    q = normalize_query_text(query)
    q = re.sub(r'[?.,!:]', '', q)
    targets: list[str] = []
    seen: set[str] = set()
    
    # Get all vehicles
    rows = _vehicle_name_rows(db)
    
    # Priority 1: Full Name match
    for brand, model in rows:
        fn = f"{(brand or '').lower()} {(model or '').lower()}".strip()
        if fn and fn in q and fn not in seen:
            seen.add(fn)
            targets.append(fn)

    # Priority 2: Brand/Alias + Model match
    if len(targets) < 2:
        for brand, model in rows:
            brand_l = (brand or "").lower()
            model_l = (model or "").lower()
            if not model_l or model_l in seen: continue
            
            check_brand = False
            for alias, targets_alias in BRAND_ALIASES.items():
                if alias in q and any(t in brand_l for t in targets_alias):
                    check_brand = True
                    break
            
            # If brand alias found and model found
            if check_brand and f" {model_l} " in f" {q} ":
                seen.add(model_l)
                targets.append(f"{brand_l} {model_l}")

    # Priority 3: Model alone
    if len(targets) < 4:
        for brand, model in rows:
            model_l = (model or "").lower()
            if len(model_l) >= 4 and f" {model_l} " in f" {q} " and model_l not in seen:
                seen.add(model_l)
                targets.append(model_l)
                
    return targets[:4]


def is_pronoun_query(query: str) -> bool:
    q = normalize_query_text(query)
    return re.search(r"\b(it|its|this|that|this one|that one|that ev|this ev)\b", q) is not None


def is_list_query(query: str) -> bool:
    q = normalize_query_text(query)
    return any(
        phrase in q
        for phrase in ["list all", "overall list", "all evs", "all vehicles", "entire list", "full list", "show all evs"]
    )


def should_use_grounded_fallback(query: str, plan: QueryPlan | None = None) -> bool:
    return False


def detect_expertise(query: str) -> str:
    q = normalize_query_text(query)
    expert_terms = ["nm", "torque", "chemistry", "pmsm", "ah", "density", "tco", "lifecycle", "c-rating", "bms"]
    enthusiast_terms = ["kwh", "charging", "battery", "top speed", "kw", "efficiency", "ground clearance", "lfp", "nmc"]
    expert_hits = sum(1 for term in expert_terms if term in q)
    enthusiast_hits = sum(1 for term in enthusiast_terms if term in q)
    if expert_hits >= 2:
        return "Expert"
    if expert_hits >= 1 or enthusiast_hits >= 2:
        return "Enthusiast"
    return "Novice"


def build_query_plan(query: str, db: Session) -> QueryPlan:
    q = normalize_query_text(query)
    plan = QueryPlan(intent="general")
    plan.budget_min, plan.budget_max = infer_budget(q)
    plan.min_range_km = infer_range_km(q)
    plan.segment = infer_segment(q)
    plan.city = infer_city(q)

    if is_greeting(q):
        plan.intent = "greeting"
        return plan

    if is_list_query(q):
        plan.intent = "inventory"
        return plan

    if is_location_query(q):
        plan.intent = "location"
        return plan

    if is_vehicle_compare_query(q, db):
        plan.intent = "vehicle_compare"
    elif is_concept_compare_query(q, db):
        plan.intent = "concept_compare"
    elif "subsidy" in q or "fame" in q or "pm e-drive" in q:
        plan.intent = "subsidy"
    elif needs_explicit_vehicle(q) and has_known_vehicle_reference(q, db):
        plan.intent = "spec"
    elif any(token in q for token in KNOWLEDGE_HINTS) or ("what is" in q and is_domain_query(q)):
        plan.intent = "knowledge"
    elif any(token in q for token in ["best", "recommend", "under", "budget", "top range", "longest range", "good for"]):
        plan.intent = "recommend"
    elif plan.segment and any(token in q for token in ["good", "daily", "commute", "city"]):
        plan.intent = "recommend"
    elif has_known_vehicle_reference(q, db):
        plan.intent = "spec"

    plan.compare_targets = extract_compare_targets(q, db)

    if plan.intent == "vehicle_compare" and len(plan.compare_targets) < 2 and not detect_explicit_vehicle(query, db):
        plan.needs_clarification = True
        plan.clarification_question = "Please share two EV model or brand names to compare (e.g., Ola S1 Pro vs Ather 450X)."

    if plan.intent == "spec" and not has_known_vehicle_reference(q, db):
        plan.needs_clarification = True
        plan.clarification_question = "Please share the exact EV model name so I can give precise specs from the current dataset."

    if plan.intent == "recommend" and plan.segment is None and plan.budget_max is None and plan.budget_min is None and not has_known_vehicle_reference(query, db):
        plan.needs_clarification = True
        plan.clarification_question = "Tell me at least one preference: segment, budget, range, or city, and I will give accurate EV options."

    return plan
