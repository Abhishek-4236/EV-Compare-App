from __future__ import annotations

import re
from difflib import SequenceMatcher

from .embeddings import embed_text_if_ready
from .ev_policy import estimate_segment_support
from .ev_rag_types import ParsedQuery, RetrievalMatch, VehicleDocument
from .faiss_store import FaissStore


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def vehicle_aliases(vehicle: VehicleDocument) -> list[str]:
    aliases = [
        vehicle.name,
        f"{vehicle.brand} {vehicle.model}",
        vehicle.model,
    ]
    if vehicle.brand and vehicle.model.startswith(vehicle.brand):
        aliases.append(vehicle.model[len(vehicle.brand):].strip())
    return [normalize_text(alias) for alias in aliases if alias]


def contains_vehicle_mention(query: str, vehicle: VehicleDocument) -> bool:
    normalized_query = f" {normalize_text(query)} "
    for alias in vehicle_aliases(vehicle):
        if alias and f" {alias} " in normalized_query:
            return True
    return False


def resolve_named_vehicles(query: str, vehicles: list[VehicleDocument]) -> list[VehicleDocument]:
    exact: list[VehicleDocument] = []
    seen: set[str] = set()
    for vehicle in vehicles:
        if contains_vehicle_mention(query, vehicle) and vehicle.id not in seen:
            seen.add(vehicle.id)
            exact.append(vehicle)
    return exact


def closest_vehicle_candidates(query_name: str, vehicles: list[VehicleDocument], limit: int = 3) -> list[VehicleDocument]:
    normalized_query = normalize_text(query_name)
    scored: list[tuple[float, VehicleDocument]] = []
    for vehicle in vehicles:
        haystack = normalize_text(vehicle.name)
        score = SequenceMatcher(None, normalized_query, haystack).ratio()
        if score >= 0.55:
            scored.append((score, vehicle))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [vehicle for _, vehicle in scored[:limit]]


def vehicle_matches_type(vehicle: VehicleDocument, requested_type: str | None) -> bool:
    if not requested_type:
        return True
    requested = requested_type.lower()
    category = str(vehicle.metadata.get("category") or "").upper()
    vehicle_type = (vehicle.vehicle_type or "").lower()

    if requested == "car":
        return category == "4W" and not any(token in vehicle_type for token in ["commercial", "cargo", "truck", "pickup", "fleet"])
    if requested == "bike":
        return category == "2W" and "scooter" not in vehicle_type
    if requested == "scooter":
        return category == "2W" and "scooter" in vehicle_type
    if requested == "three_wheeler":
        return category == "3W"
    if requested == "truck":
        return category == "TRUCK"
    if requested == "bus":
        return category == "BUS"
    if requested == "commercial":
        return category in {"3W", "TRUCK", "BUS"} or any(token in vehicle_type for token in ["commercial", "cargo", "fleet"])
    return vehicle_type == requested


def is_personal_car_candidate(vehicle: VehicleDocument) -> bool:
    category = str(vehicle.metadata.get("category") or "").upper()
    if category != "4W":
        return False
    text = " ".join(
        part
        for part in [vehicle.name, vehicle.brand, vehicle.model, vehicle.vehicle_type]
        if part
    ).lower()
    blocked_tokens = ["commercial", "cargo", "truck", "pickup", "fleet", "taxi", "xpres", "zor", "ace ev"]
    return not any(token in text for token in blocked_tokens)


def vehicle_supports_fast_charging(vehicle: VehicleDocument) -> bool:
    charging_type = (vehicle.charging_type or "").lower()
    charging_time = (vehicle.charging_time or "").lower()
    text = f"{charging_type} {charging_time}"
    return any(token in text for token in ["dc", "fast", "ccs2", "1 hr", "50 min", "40 min", "30 min"])


def apply_vehicle_filters(vehicles: list[VehicleDocument], parsed: ParsedQuery) -> list[VehicleDocument]:
    filtered = list(vehicles)
    filters = parsed.filters

    if filters.vehicle_type:
        filtered = [vehicle for vehicle in filtered if vehicle_matches_type(vehicle, filters.vehicle_type)]
        if filters.vehicle_type == "car":
            filtered = [vehicle for vehicle in filtered if is_personal_car_candidate(vehicle)]
    if filters.brand:
        brand_lower = filters.brand.lower()
        filtered = [vehicle for vehicle in filtered if brand_lower in vehicle.brand.lower()]
    if filters.max_price_inr is not None:
        filtered = [vehicle for vehicle in filtered if vehicle.price_inr is not None and vehicle.price_inr <= filters.max_price_inr]
    if filters.min_price_inr is not None:
        filtered = [vehicle for vehicle in filtered if vehicle.price_inr is not None and vehicle.price_inr >= filters.min_price_inr]
    if filters.min_range_km is not None:
        filtered = [vehicle for vehicle in filtered if vehicle.range_km is not None and vehicle.range_km >= filters.min_range_km]
    if filters.fast_charging:
        filtered = [vehicle for vehicle in filtered if vehicle_supports_fast_charging(vehicle)]
    if filters.charging_type == "ac":
        filtered = [vehicle for vehicle in filtered if not vehicle_supports_fast_charging(vehicle)]

    return filtered


def _required_range(parsed: ParsedQuery) -> int:
    filters = parsed.filters
    if filters.min_range_km is not None:
        return filters.min_range_km

    daily_distance = filters.daily_distance_km
    use_cases = set(filters.use_cases)
    home_charging = filters.home_charging

    if daily_distance:
        multiplier = 2.6 if home_charging is False else 1.8
        if {"highway", "weekend", "family"} & use_cases:
            multiplier = max(multiplier, 3.1)
        return max(100, int(daily_distance * multiplier))

    if {"highway", "weekend", "family"} & use_cases:
        return 280
    if {"city", "office", "daily_commute", "college"} & use_cases:
        return 110
    return 0


def _budget_score(price_inr: int | None, parsed: ParsedQuery) -> float:
    if price_inr is None:
        return -2.0

    filters = parsed.filters
    score = 0.0
    if filters.max_price_inr is not None:
        gap = max(filters.max_price_inr - price_inr, 0)
        score += 3.5 + min(gap / max(filters.max_price_inr, 1), 1.0)
    else:
        score += max(0.0, 2.5 - min(price_inr / 2500000, 2.5))
    if filters.min_price_inr is not None and price_inr >= filters.min_price_inr:
        score += 1.0
    return score


def _use_case_score(vehicle: VehicleDocument, parsed: ParsedQuery) -> float:
    score = 0.0
    category = str(vehicle.metadata.get("category") or "").upper()
    price_inr = vehicle.price_inr or 0
    range_km = vehicle.range_km or 0
    use_cases = set(parsed.filters.use_cases)

    if {"city", "office", "daily_commute"} & use_cases:
        if category in {"2W", "4W"}:
            score += 2.0
        if price_inr and price_inr <= 1500000:
            score += 1.5

    if {"family", "highway", "weekend"} & use_cases:
        if category == "4W":
            score += 3.0
        if range_km >= 300:
            score += 2.5
        else:
            score -= 2.0
        if vehicle_supports_fast_charging(vehicle):
            score += 1.5

    if {"college"} & use_cases:
        if category == "2W":
            score += 3.0
        if price_inr <= 150000:
            score += 1.5

    if {"delivery", "cargo", "fleet"} & use_cases:
        if category in {"3W", "TRUCK"} or (vehicle.vehicle_type or "").lower() == "commercial":
            score += 3.5
        else:
            score -= 4.0

    return score


def _charging_score(vehicle: VehicleDocument, parsed: ParsedQuery) -> float:
    score = 0.0
    if parsed.filters.home_charging is False:
        score += 2.2 if vehicle_supports_fast_charging(vehicle) else -2.8
    if parsed.filters.fast_charging:
        score += 2.0 if vehicle_supports_fast_charging(vehicle) else -5.0
    return score


def _range_score(vehicle: VehicleDocument, parsed: ParsedQuery) -> float:
    required_range = _required_range(parsed)
    range_km = vehicle.range_km or 0

    if required_range <= 0:
        return min(range_km / 120, 2.0)
    if range_km < required_range:
        return -4.5
    return 3.0 + min((range_km - required_range) / 120, 2.0)


def _state_score(vehicle: VehicleDocument, parsed: ParsedQuery) -> float:
    if not parsed.filters.state:
        return 0.0
    central_support, state_support = estimate_segment_support(vehicle, parsed.filters.state)
    total_support = central_support + state_support
    return min(total_support / 20000, 1.6)


def candidate_score(vehicle: VehicleDocument, parsed: ParsedQuery, query: str) -> float:
    q = normalize_text(query)
    vehicle_text = normalize_text(f"{vehicle.name} {vehicle.brand} {vehicle.model} {vehicle.vehicle_type}")
    overlap = len(set(q.split()).intersection(set(vehicle_text.split())))

    score = overlap * 0.5
    score += _budget_score(vehicle.price_inr, parsed)
    score += _range_score(vehicle, parsed)
    score += _use_case_score(vehicle, parsed)
    score += _charging_score(vehicle, parsed)
    score += _state_score(vehicle, parsed)

    if parsed.filters.vehicle_type and vehicle_matches_type(vehicle, parsed.filters.vehicle_type):
        score += 2.5
    if parsed.sort_by == "price":
        score += max(0.0, 3.0 - min((vehicle.price_inr or 0) / 500000, 3.0))
    if parsed.sort_by == "range":
        score += min((vehicle.range_km or 0) / 110, 3.0)

    return score


def hybrid_retrieve(
    query: str,
    parsed: ParsedQuery,
    vehicles: list[VehicleDocument],
    store: FaissStore | None,
    top_k: int = 5,
) -> list[RetrievalMatch]:
    filtered = apply_vehicle_filters(vehicles, parsed)
    if not filtered:
        return []

    lexical_ranked = sorted(
        filtered,
        key=lambda vehicle: candidate_score(vehicle, parsed, query),
        reverse=True,
    )

    vector_scores: dict[str, float] = {}
    if store is not None:
        try:
            embedding = embed_text_if_ready(query)
            if embedding is not None:
                for vehicle_id, score in store.search(embedding, top_k=max(top_k * 3, 12)):
                    vector_scores[vehicle_id] = score
        except Exception:
            vector_scores = {}

    matches: list[RetrievalMatch] = []
    for vehicle in lexical_ranked[: max(top_k * 3, 12)]:
        combined_score = candidate_score(vehicle, parsed, query) + vector_scores.get(vehicle.id, 0.0) * 0.4
        matched_on = ["rank"]
        if parsed.filters.vehicle_type:
            matched_on.append("segment")
        if parsed.filters.max_price_inr is not None or parsed.filters.min_price_inr is not None:
            matched_on.append("budget")
        if parsed.filters.fast_charging:
            matched_on.append("fast_charging")
        if parsed.filters.state:
            matched_on.append("state")
        matches.append(RetrievalMatch(vehicle=vehicle, score=combined_score, matched_on=matched_on))

    if parsed.sort_by == "price":
        matches.sort(key=lambda item: ((item.vehicle.price_inr or 10**12), -item.score))
    elif parsed.sort_by == "range":
        matches.sort(key=lambda item: (-(item.vehicle.range_km or 0), -item.score))
    else:
        matches.sort(key=lambda item: item.score, reverse=True)
    return matches[:top_k]
