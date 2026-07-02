from __future__ import annotations

import re

from .ev_rag_types import ParsedQuery, RetrievalMatch


STRICT_NO_DATA_MESSAGE = "Not enough data available"


def validate_grounding(
    answer: str,
    fallback_answer: str,
    context_chunks: list[str],
    matches: list[RetrievalMatch],
) -> str:
    if not context_chunks and not matches:
        return STRICT_NO_DATA_MESSAGE

    supported_text = " ".join([fallback_answer, *context_chunks]).lower()
    answer_text = (answer or "").strip()
    if not answer_text:
        return fallback_answer

    vehicle_names = [match.vehicle.name for match in matches]
    unsupported_names = [
        name
        for name in re.findall(r"\b[A-Z][A-Za-z0-9+-]*(?:\s+[A-Z][A-Za-z0-9+-]*){1,4}\b", answer_text)
        if any(token in name.lower() for token in ["ev", "tata", "mg", "byd", "kia", "hyundai", "ather", "ola"])
        and name.lower() not in supported_text
    ]
    if unsupported_names:
        return fallback_answer

    for number in re.findall(r"\b\d+(?:\.\d+)?\b", answer_text):
        if number not in supported_text:
            return fallback_answer

    if vehicle_names and not any(name.lower() in answer_text.lower() for name in vehicle_names):
        return fallback_answer
    return answer_text


def confidence_level(parsed: ParsedQuery, matches: list[RetrievalMatch]) -> str:
    if not matches:
        return "low"
    if parsed.intent == "comparison":
        return "high" if len(matches) >= 2 else "low"
    if parsed.intent == "recommendation":
        has_category = bool(parsed.filters.vehicle_type)
        has_budget = parsed.filters.max_price_inr is not None or parsed.filters.min_price_inr is not None
        has_usage = bool(parsed.filters.use_cases) or parsed.filters.daily_distance_km is not None
        has_priority = bool(parsed.filters.priority or parsed.sort_by)
        if has_category and has_budget and (has_usage or has_priority):
            return "high"
        if has_category and has_budget:
            return "medium"
        return "low"
    return "high"
