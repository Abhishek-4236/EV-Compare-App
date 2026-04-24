from __future__ import annotations

import re

from .ev_rag_types import ParsedQuery, QueryFilters


TYPE_HINTS: list[tuple[str, str]] = [
    ("three wheeler", "three_wheeler"),
    ("3 wheeler", "three_wheeler"),
    ("3-wheeler", "three_wheeler"),
    ("e-rickshaw", "three_wheeler"),
    ("rickshaw", "three_wheeler"),
    ("scooter", "scooter"),
    ("scooty", "scooter"),
    ("motorcycle", "bike"),
    ("bike", "bike"),
    ("family car", "car"),
    ("hatchback", "car"),
    ("sedan", "car"),
    ("suv", "car"),
    ("car", "car"),
    ("truck", "truck"),
    ("bus", "bus"),
    ("commercial", "commercial"),
    ("cargo", "commercial"),
    ("fleet", "commercial"),
]

STATE_ALIASES = {
    "andhra pradesh": "andhra pradesh",
    "arunachal pradesh": "arunachal pradesh",
    "assam": "assam",
    "bihar": "bihar",
    "chandigarh": "chandigarh",
    "chhattisgarh": "chhattisgarh",
    "delhi": "delhi",
    "goa": "goa",
    "gujarat": "gujarat",
    "haryana": "haryana",
    "himachal pradesh": "himachal pradesh",
    "jammu and kashmir": "jammu and kashmir",
    "jharkhand": "jharkhand",
    "karnataka": "karnataka",
    "kerala": "kerala",
    "ladakh": "ladakh",
    "maharashtra": "maharashtra",
    "madhya pradesh": "madhya pradesh",
    "odisha": "odisha",
    "orissa": "odisha",
    "punjab": "punjab",
    "rajasthan": "rajasthan",
    "tamil nadu": "tamil nadu",
    "telangana": "telangana",
    "uttar pradesh": "uttar pradesh",
    "up": "uttar pradesh",
    "uttarakhand": "uttarakhand",
    "west bengal": "west bengal",
}

USE_CASE_HINTS = {
    "city": ["city", "urban"],
    "office": ["office", "work commute", "daily office", "to office"],
    "daily_commute": ["daily", "commute", "per day", "a day", "every day"],
    "family": ["family", "kids", "parents"],
    "highway": ["highway", "road trip", "intercity"],
    "weekend": ["weekend", "long trip", "occasional trip"],
    "college": ["college", "student"],
    "delivery": ["delivery", "courier", "parcel"],
    "cargo": ["cargo", "goods", "load"],
    "fleet": ["fleet", "taxi", "cab", "business"],
}

COMPARISON_PATTERNS = [
    r"\bcompare\b",
    r"\bversus\b",
    r"\bvs\b",
    r"\bdifference\s+between\b",
    r"\bbetter than\b",
]

INFO_PATTERNS = [
    "what is",
    "explain",
    "how does",
    "how do",
    "why does",
    "tco",
    "total cost of ownership",
    "subsidy",
    "charging",
    "limitations",
]


def _parse_price_amount(amount_text: str, unit: str | None) -> int:
    amount = float(amount_text)
    normalized_unit = (unit or "").lower()
    if normalized_unit in {"lakh", "lakhs", "lac", "lacs", "l"}:
        return int(amount * 100000)
    if normalized_unit == "k":
        return int(amount * 1000)
    if amount < 1000:
        return int(amount * 100000)
    return int(amount)


def _extract_price_filters(query: str) -> tuple[int | None, int | None]:
    q = (query or "").lower()

    range_patterns = [
        r"(?:between|from)\s*₹?\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|l|k)?\s*(?:to|-|–)\s*₹?\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|l|k)?",
        r"₹?\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|l|k)?\s*(?:to|-|–)\s*₹?\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|l|k)\b",
    ]
    for pattern in range_patterns:
        match = re.search(pattern, q)
        if not match:
            continue
        left_value = _parse_price_amount(match.group(1), match.group(2) or match.group(4))
        right_value = _parse_price_amount(match.group(3), match.group(4) or match.group(2))
        return min(left_value, right_value), max(left_value, right_value)

    under_match = re.search(r"(?:under|below|less than|max(?:imum)? of)\s*₹?\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|l|k)?", q)
    if under_match:
        return None, _parse_price_amount(under_match.group(1), under_match.group(2))

    budget_match = re.search(r"(?:budget|priced?|price point)(?:\s*(?:is|of|around|about|near|at))?\s*₹?\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|l|k)?", q)
    if budget_match:
        return None, _parse_price_amount(budget_match.group(1), budget_match.group(2))

    above_match = re.search(r"(?:above|over|more than|min(?:imum)? of)\s*₹?\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|l|k)?", q)
    if above_match:
        return _parse_price_amount(above_match.group(1), above_match.group(2)), None

    return None, None


def _extract_daily_distance(query: str) -> int | None:
    q = (query or "").lower()
    patterns = [
        r"(\d+)\s*km\s*(?:daily|a day|per day|every day)",
        r"(?:daily|a day|per day)\s*(?:of|around|about)?\s*(\d+)\s*km",
        r"travel\s*(\d+)\s*km",
        r"commute\s*(\d+)\s*km",
    ]
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            return int(match.group(1))
    return None


def _extract_range_requirement(query: str, daily_distance_km: int | None) -> int | None:
    q = (query or "").lower()
    explicit_range = re.search(r"(\d+)\s*km\s*(?:range)?", q)
    if explicit_range and any(token in q for token in ["range", "minimum", "at least", "above"]):
        return int(explicit_range.group(1))
    if daily_distance_km and any(token in q for token in ["daily", "commute", "per day", "a day"]):
        return max(100, int(daily_distance_km * 2))
    return None


def _extract_vehicle_type(query: str) -> str | None:
    q = (query or "").lower()
    for token, mapped in TYPE_HINTS:
        if token in q:
            return mapped
    return None


def _extract_state(query: str) -> str | None:
    q = re.sub(r"\s+", " ", (query or "").lower()).strip()
    ordered_aliases = sorted(STATE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True)
    for alias, normalized in ordered_aliases:
        if re.search(rf"\b{re.escape(alias)}\b", q):
            return normalized
    return None


def _extract_use_cases(query: str) -> list[str]:
    q = (query or "").lower()
    use_cases: list[str] = []
    for label, hints in USE_CASE_HINTS.items():
        if any(hint in q for hint in hints):
            use_cases.append(label)
    return list(dict.fromkeys(use_cases))


def _extract_home_charging(query: str) -> bool | None:
    q = (query or "").lower()
    negative_patterns = [
        "no home charging",
        "without home charging",
        "dont have home charging",
        "don't have home charging",
        "cannot charge at home",
        "can't charge at home",
        "street parking",
    ]
    if any(pattern in q for pattern in negative_patterns):
        return False
    positive_patterns = [
        "with home charging",
        "home charging",
        "charge at home",
        "home charger",
        "charging at home",
    ]
    if any(pattern in q for pattern in positive_patterns):
        return True
    return None


def _extract_fast_charging(query: str) -> tuple[bool | None, str | None]:
    q = (query or "").lower()
    if any(token in q for token in ["fast charging only", "fast charger only", "dc fast charging", "dc charging", "fast charging"]):
        return True, "dc_fast"
    if any(token in q for token in ["ac charging", "slow charging"]):
        return False, "ac"
    return None, None


def _extract_brand(query: str) -> str | None:
    q = (query or "").lower()
    known_brands = [
        "ather",
        "bajaj",
        "byd",
        "hero",
        "hyundai",
        "kia",
        "mahindra",
        "mg",
        "ola",
        "revolt",
        "tata",
        "tvs",
    ]
    for brand in known_brands:
        if re.search(rf"\b{re.escape(brand)}\b", q):
            return brand.title() if brand != "mg" else "MG"
    return None


def parse_user_query(query: str) -> ParsedQuery:
    text = (query or "").strip()
    q = text.lower()

    min_price_inr, max_price_inr = _extract_price_filters(text)
    daily_distance_km = _extract_daily_distance(q)
    min_range_km = _extract_range_requirement(q, daily_distance_km)
    vehicle_type = _extract_vehicle_type(q)
    state = _extract_state(q)
    use_cases = _extract_use_cases(q)
    home_charging = _extract_home_charging(q)
    fast_charging, charging_type = _extract_fast_charging(q)
    brand = _extract_brand(q)

    if vehicle_type is None and {"family", "highway", "weekend"} & set(use_cases):
        vehicle_type = "car"

    intent = "info"
    if any(re.search(pattern, q) for pattern in COMPARISON_PATTERNS):
        intent = "comparison"
    elif any(token in q for token in ["best", "recommend", "suggest", "what should i buy", "which ev", "practical", "good for", "shortlist", "under ", "i want", "looking for", "need an ev", "need a"]):
        intent = "recommendation"
    elif any(token in q for token in INFO_PATTERNS):
        intent = "info"

    if daily_distance_km and intent == "info":
        intent = "recommendation"
    if intent == "info" and (vehicle_type or min_price_inr is not None or max_price_inr is not None or use_cases):
        intent = "recommendation"

    sort_by = None
    if any(token in q for token in ["cheap", "cheapest", "budget", "affordable"]):
        sort_by = "price"
    elif any(token in q for token in ["range", "longest", "long range", "highway"]):
        sort_by = "range"

    return ParsedQuery(
        intent=intent,  # type: ignore[arg-type]
        rewritten_query=text,
        filters=QueryFilters(
            min_price_inr=min_price_inr,
            max_price_inr=max_price_inr,
            min_range_km=min_range_km,
            vehicle_type=vehicle_type,
            brand=brand,
            charging_type=charging_type,
            fast_charging=fast_charging,
            state=state,
            daily_distance_km=daily_distance_km,
            home_charging=home_charging,
            use_cases=use_cases,
        ),
        vehicle_names=[],
        sort_by=sort_by,
        user_goal=text,
    )
