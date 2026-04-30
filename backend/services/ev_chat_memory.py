from __future__ import annotations

import re

from pydantic import BaseModel, Field

from .ev_rag_types import ParsedQuery, QueryFilters
from .query_parser import parse_user_query


FOLLOW_UP_PREFIXES = (
    "and ",
    "also ",
    "give ",
    "show ",
    "put ",
    "convert ",
    "what about",
    "now ",
    "make it",
    "with ",
    "without ",
    "keep ",
    "same ",
    "only ",
)


class SessionMemory(BaseModel):
    filters: QueryFilters = Field(default_factory=QueryFilters)
    last_intent: str = "info"


def _merge_use_cases(existing: list[str], incoming: list[str]) -> list[str]:
    return list(dict.fromkeys(existing + incoming))


def _looks_like_follow_up(query: str) -> bool:
    normalized = (query or "").strip().lower()
    return normalized.startswith(FOLLOW_UP_PREFIXES) or bool(re.fullmatch(r"(yes|no|sure|okay|ok)", normalized))


def build_session_memory(chat_history: list[dict[str, str]] | None) -> SessionMemory:
    memory = SessionMemory()
    history = chat_history or []

    for item in history:
        role = (item.get("role") or "").lower()
        if role != "user":
            continue
        parsed = parse_user_query(item.get("content") or item.get("text") or "")
        memory.last_intent = parsed.intent

        if parsed.filters.min_price_inr is not None:
            memory.filters.min_price_inr = parsed.filters.min_price_inr
        if parsed.filters.max_price_inr is not None:
            memory.filters.max_price_inr = parsed.filters.max_price_inr
        if parsed.filters.min_range_km is not None:
            memory.filters.min_range_km = parsed.filters.min_range_km
        if parsed.filters.vehicle_type:
            memory.filters.vehicle_type = parsed.filters.vehicle_type
        if parsed.filters.brand:
            memory.filters.brand = parsed.filters.brand
        if parsed.filters.charging_type:
            memory.filters.charging_type = parsed.filters.charging_type
        if parsed.filters.fast_charging is not None:
            memory.filters.fast_charging = parsed.filters.fast_charging
        if parsed.filters.state:
            memory.filters.state = parsed.filters.state
        if parsed.filters.daily_distance_km is not None:
            memory.filters.daily_distance_km = parsed.filters.daily_distance_km
        if parsed.filters.home_charging is not None:
            memory.filters.home_charging = parsed.filters.home_charging
        if parsed.filters.use_cases:
            memory.filters.use_cases = _merge_use_cases(memory.filters.use_cases, parsed.filters.use_cases)

    return memory


def apply_session_memory(query: str, parsed: ParsedQuery, memory: SessionMemory) -> ParsedQuery:
    if not _looks_like_follow_up(query):
        return parsed

    filters = parsed.filters.model_copy(deep=True)
    remembered = memory.filters

    if filters.min_price_inr is None:
        filters.min_price_inr = remembered.min_price_inr
    if filters.max_price_inr is None:
        filters.max_price_inr = remembered.max_price_inr
    if filters.min_range_km is None:
        filters.min_range_km = remembered.min_range_km
    if not filters.vehicle_type:
        filters.vehicle_type = remembered.vehicle_type
    if not filters.brand:
        filters.brand = remembered.brand
    if not filters.charging_type:
        filters.charging_type = remembered.charging_type
    if filters.fast_charging is None:
        filters.fast_charging = remembered.fast_charging
    if not filters.state:
        filters.state = remembered.state
    if filters.daily_distance_km is None:
        filters.daily_distance_km = remembered.daily_distance_km
    if filters.home_charging is None:
        filters.home_charging = remembered.home_charging
    filters.use_cases = _merge_use_cases(remembered.use_cases, filters.use_cases)

    intent = parsed.intent
    if intent == "info" and memory.last_intent in {"recommendation", "comparison"}:
        intent = memory.last_intent  # type: ignore[assignment]

    return parsed.model_copy(update={"intent": intent, "filters": filters})


def needs_recommendation_clarification(query: str, parsed: ParsedQuery) -> bool:
    q = re.sub(r"\s+", " ", (query or "").strip().lower())
    filters = parsed.filters
    has_budget = filters.max_price_inr is not None or filters.min_price_inr is not None
    has_segment = bool(filters.vehicle_type)
    has_use_case = bool(filters.use_cases)
    has_distance = filters.daily_distance_km is not None

    if parsed.intent != "recommendation":
        return False

    if q in {"best ev", "which ev", "which one should i buy", "what should i buy"}:
        return True

    if not has_segment and not has_budget:
        return True

    if not has_segment and has_budget and not has_use_case:
        return True

    return False
