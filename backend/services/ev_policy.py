from __future__ import annotations

from .ev_rag_types import VehicleDocument


STATE_SUBSIDY_DEFAULTS = {
    "andhra pradesh": 15000,
    "arunachal pradesh": 0,
    "assam": 10000,
    "bihar": 10000,
    "chandigarh": 15000,
    "chhattisgarh": 5000,
    "delhi": 36000,
    "goa": 20000,
    "gujarat": 25000,
    "haryana": 15000,
    "himachal pradesh": 10000,
    "jammu and kashmir": 10000,
    "jharkhand": 5000,
    "karnataka": 25000,
    "kerala": 15000,
    "ladakh": 0,
    "maharashtra": 30000,
    "madhya pradesh": 10000,
    "odisha": 15000,
    "punjab": 10000,
    "rajasthan": 15000,
    "tamil nadu": 20000,
    "telangana": 20000,
    "uttar pradesh": 20000,
    "uttarakhand": 15000,
    "west bengal": 15000,
}

POLICY_META = {
    "central_scheme": "EViq policy snapshot",
    "last_updated": "2026-04-09",
    "notes": "Treat state incentives as indicative policy context only and verify the latest dealer quotation.",
}


def normalize_state_name(state: str | None) -> str | None:
    if not state:
        return None
    normalized = " ".join(state.lower().split())
    if normalized == "orissa":
        return "odisha"
    if normalized == "up":
        return "uttar pradesh"
    return normalized


def get_state_policy_note(state: str | None) -> str | None:
    normalized = normalize_state_name(state)
    if not normalized:
        return None
    amount = STATE_SUBSIDY_DEFAULTS.get(normalized)
    if amount is None:
        return None
    return f"{normalized.title()} policy snapshot: about ₹{amount:,} indicative state support."


def estimate_segment_support(vehicle: VehicleDocument, state: str | None) -> tuple[int, int]:
    category = str(vehicle.metadata.get("category") or "").upper()
    state_support = STATE_SUBSIDY_DEFAULTS.get(normalize_state_name(state) or "", 0)

    central_support = 0
    if category == "2W":
        central_support = min(5000, int((vehicle.battery_kwh or 0) * 2500))
    elif category == "3W":
        central_support = 12500

    return central_support, state_support
