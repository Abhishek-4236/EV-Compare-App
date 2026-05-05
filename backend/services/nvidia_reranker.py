from __future__ import annotations

import json
import logging
from urllib import error, request

from core.config import settings

from .ev_rag_types import RetrievalMatch

logger = logging.getLogger(__name__)


def _vehicle_passage(match: RetrievalMatch) -> str:
    vehicle = match.vehicle
    parts = [
        vehicle.content,
        f"Vehicle name: {vehicle.name}",
        f"Brand: {vehicle.brand}",
        f"Model: {vehicle.model}",
        f"Type: {vehicle.vehicle_type}",
        f"Price INR: {vehicle.price_inr}" if vehicle.price_inr is not None else None,
        f"Range km: {vehicle.range_km}" if vehicle.range_km is not None else None,
        f"Battery kWh: {vehicle.battery_kwh}" if vehicle.battery_kwh is not None else None,
        f"Charging time: {vehicle.charging_time}" if vehicle.charging_time else None,
        f"Charging type: {vehicle.charging_type}" if vehicle.charging_type else None,
        f"Features: {', '.join(vehicle.features)}" if vehicle.features else None,
    ]
    return ". ".join(part for part in parts if part)


def is_nvidia_rerank_configured() -> bool:
    return bool(settings.NVIDIA_RERANK_ENABLED and settings.NVIDIA_API_KEY)


def nvidia_rerank_matches(query: str, matches: list[RetrievalMatch], top_k: int) -> list[RetrievalMatch]:
    if not is_nvidia_rerank_configured() or len(matches) <= 1:
        return matches[:top_k]

    candidate_limit = max(top_k, min(settings.NVIDIA_RERANK_MAX_CANDIDATES, len(matches)))
    candidates = matches[:candidate_limit]
    endpoint = settings.NVIDIA_RERANK_URL or (settings.NVIDIA_API_BASE.rstrip("/") + "/v1/ranking")
    payload = {
        "model": settings.NVIDIA_RERANK_MODEL,
        "query": {"text": query},
        "passages": [{"text": _vehicle_passage(match)} for match in candidates],
        "truncate": "END",
    }
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=settings.NVIDIA_RERANK_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, error.HTTPError, json.JSONDecodeError) as exc:
        logger.warning("NVIDIA rerank failed; using local reranker fallback: %s", exc)
        return matches[:top_k]

    rankings = body.get("rankings") or body.get("data") or []
    reranked: list[RetrievalMatch] = []
    used_indexes: set[int] = set()
    for item in rankings:
        try:
            index = int(item.get("index"))
        except (AttributeError, TypeError, ValueError):
            continue
        if index < 0 or index >= len(candidates) or index in used_indexes:
            continue
        used_indexes.add(index)
        raw_score = item.get("logit", item.get("score", item.get("relevance_score", candidates[index].score)))
        try:
            nvidia_score = float(raw_score)
        except (TypeError, ValueError):
            nvidia_score = candidates[index].score
        reranked.append(
            candidates[index].model_copy(
                update={
                    "score": nvidia_score,
                    "matched_on": list(dict.fromkeys([*candidates[index].matched_on, "nvidia_rerank"])),
                }
            )
        )

    if len(reranked) < top_k:
        for index, match in enumerate(candidates):
            if index not in used_indexes:
                reranked.append(match)
            if len(reranked) >= top_k:
                break

    return reranked[:top_k]
