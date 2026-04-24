from __future__ import annotations

from .ev_chat_knowledge import KnowledgeArticle, extract_supporting_lines
from .ev_policy import estimate_segment_support, get_state_policy_note
from .ev_rag_types import ParsedQuery, RetrievalMatch, VehicleDocument


def format_price(price_inr: int | None) -> str:
    if price_inr is None:
        return "Price unavailable"
    if price_inr >= 100000:
        return f"₹{price_inr / 100000:.2f} lakh"
    return f"₹{price_inr:,}"


def format_vehicle_snapshot(vehicle: VehicleDocument) -> str:
    parts = [format_price(vehicle.price_inr)]
    if vehicle.range_km is not None:
        parts.append(f"{vehicle.range_km} km range")
    if vehicle.battery_kwh is not None:
        parts.append(f"{vehicle.battery_kwh:.1f} kWh battery")
    if vehicle.charging_time:
        parts.append(f"{vehicle.charging_time} charging")
    return ", ".join(parts)


def build_clarification_answer(query: str, parsed: ParsedQuery) -> str:
    if parsed.intent == "comparison":
        return (
            "I can compare EVs, but I need the exact two model names from the current dataset.\n\n"
            "Tell me both models directly, for example: `Compare Tata Nexon EV and MG ZS EV`."
        )

    if parsed.intent == "recommendation":
        if parsed.filters.daily_distance_km is not None:
            return (
                f"A {parsed.filters.daily_distance_km} km daily commute is very EV-friendly.\n\n"
                "To recommend the right fit, tell me your budget, whether you want a scooter/car/3-wheeler, and whether home charging is available.\n\n"
                "I can suggest the best EVs once those anchors are clear."
            )

        missing_fields: list[str] = []
        if not parsed.filters.vehicle_type:
            missing_fields.append("segment")
        if parsed.filters.max_price_inr is None and parsed.filters.min_price_inr is None:
            missing_fields.append("budget")
        if parsed.filters.home_charging is None:
            missing_fields.append("charging access")

        if missing_fields == ["segment"]:
            ask = "Tell me whether you want a scooter, bike, car, or 3-wheeler."
        elif missing_fields == ["budget"]:
            ask = "Tell me the budget you want me to stay within."
        elif missing_fields == ["charging access"]:
            ask = "Tell me whether home charging is available."
        else:
            ask = "Tell me your budget, whether you want a scooter/bike/car/3-wheeler, and whether home charging is available."

        prompt_bits = ", ".join(missing_fields) if missing_fields else "one more preference"
        return (
            f"I can build a solid EV shortlist, but I still need {prompt_bits} before I make the recommendation tighter.\n\n"
            f"{ask}\n\n"
            "I can suggest the best EVs once those anchors are clear.\n\n"
            "If you want, I can start with either `family EV car under 18 lakh` or `city scooter under 1.2 lakh`."
        )

    return (
        "I need a bit more specificity to stay grounded.\n\n"
        "Ask about a model, a comparison, a budget-based shortlist, charging, subsidies, or an EV concept like TCO."
    )


def build_inventory_answer(total: int, counts: dict[str, int]) -> str:
    parts = ", ".join(f"{key}: {value}" for key, value in sorted(counts.items()))
    return (
        f"We have {total} EV entries in the current EViq dataset.\n\n"
        f"Segment mix: {parts}.\n\n"
        "Tell me a budget, segment, charging need, or use case and I’ll narrow it down."
    )


def build_spec_answer(vehicle: VehicleDocument, parsed: ParsedQuery, query: str | None = None) -> str:
    state_note = get_state_policy_note(parsed.filters.state)
    q = (query or "").lower()
    lines = [
        f"{vehicle.name} is the closest grounded match in the current EViq dataset.",
        "",
        f"Snapshot: {format_vehicle_snapshot(vehicle)}.",
    ]
    if "top speed" in q:
        lines.extend(["", "Top speed: unavailable in the current dataset."])
    if "warranty" in q:
        lines.extend(["", "Warranty: unavailable in the current dataset."])
    if state_note:
        lines.extend(["", f"State context: {state_note}"])
    lines.extend(
        [
            "",
            "Caveat: if you need on-road price, dealer stock, or live subsidy, verify the latest quote.",
            "",
            f"Follow-up: do you want a deeper comparison against another EV in the same segment as {vehicle.name}?",
        ]
    )
    return "\n".join(lines)


def build_comparison_answer(matches: list[RetrievalMatch], parsed: ParsedQuery) -> str:
    rows = [
        "| Vehicle | Type | Price | Range | Battery | Charging |",
        "|---|---|---:|---:|---:|---|",
    ]
    for match in matches[:2]:
        vehicle = match.vehicle
        rows.append(
            f"| {vehicle.name} | {vehicle.vehicle_type} | ₹{vehicle.price_inr or 0:,} | "
            f"{vehicle.range_km or 0} km | {vehicle.battery_kwh or 0} kWh | {vehicle.charging_time or 'N/A'} |"
        )

    state_note = get_state_policy_note(parsed.filters.state)
    lead = "Here is the grounded side-by-side view from the current EViq dataset."
    caveat = "Caveat: missing or policy-sensitive fields should still be verified before purchase."
    follow_up = "Follow-up: tell me whether you care most about price, charging, highway range, or family use and I’ll name the better fit."
    pieces = [lead, "", *rows]
    if state_note:
        pieces.extend(["", f"State context: {state_note}"])
    pieces.extend(["", caveat, "", follow_up])
    return "\n".join(pieces)


def build_recommendation_answer(query: str, parsed: ParsedQuery, matches: list[RetrievalMatch]) -> str:
    top = matches[:3]
    names = ", ".join(match.vehicle.name for match in top)
    lines = [f"The strongest grounded matches for this request are {names}.", ""]

    for index, match in enumerate(top, start=1):
        vehicle = match.vehicle
        support_bits: list[str] = []
        if parsed.filters.vehicle_type:
            support_bits.append(f"fits the {parsed.filters.vehicle_type} segment")
        if parsed.filters.max_price_inr is not None and vehicle.price_inr is not None:
            support_bits.append(f"stays within the ₹{parsed.filters.max_price_inr:,} budget")
        if parsed.filters.daily_distance_km is not None and vehicle.range_km is not None:
            support_bits.append(f"has enough range for a {parsed.filters.daily_distance_km} km daily pattern")
        if parsed.filters.fast_charging and vehicle.charging_time:
            support_bits.append(f"supports fast-charging-friendly usage with {vehicle.charging_time}")
        if parsed.filters.home_charging is False:
            support_bits.append("is more practical without dependable home charging")

        direct_reason = "; ".join(support_bits) or "matches the current mix of budget, segment, and use-case filters"
        lines.append(f"{index}. **{vehicle.name}** — {format_vehicle_snapshot(vehicle)}.")
        lines.append(f"   Why it fits: {direct_reason}.")

    state_note = get_state_policy_note(parsed.filters.state)
    if state_note:
        lines.extend(["", f"State context: {state_note}"])
        central, state_support = estimate_segment_support(top[0].vehicle, parsed.filters.state)
        if central or state_support:
            lines.append(
                f"Indicative segment support on the first option: central about ₹{central:,}, state about ₹{state_support:,}."
            )

    lines.extend(
        [
            "",
            "Caveat: I am staying inside the current dataset, so live dealer pricing, final subsidy eligibility, and real-world route charging still need verification.",
            "",
            "Follow-up: if you want, I can now narrow this by lowest running cost, best highway fit, or easiest charging setup.",
        ]
    )
    return "\n".join(lines)


def build_no_match_answer(parsed: ParsedQuery) -> str:
    hints: list[str] = []
    if parsed.filters.vehicle_type:
        hints.append(parsed.filters.vehicle_type)
    if parsed.filters.max_price_inr:
        hints.append(f"under ₹{parsed.filters.max_price_inr:,}")
    if parsed.filters.min_range_km:
        hints.append(f"range above {parsed.filters.min_range_km} km")
    joined = ", ".join(hints) if hints else "your current filters"
    return (
        f"I could not find a grounded match inside {joined}.\n\n"
        "Try relaxing one filter, or tell me which requirement matters most: budget, segment, charging, or highway range."
    )


def build_out_of_domain_answer() -> str:
    return (
        "I’m specialized for EV questions on EViq India.\n\n"
        "Ask me about EV recommendations, comparisons, charging, subsidies, TCO, batteries, or a specific electric model from the current dataset."
    )


def build_knowledge_answer(query: str, article: KnowledgeArticle | None) -> str:
    q = (query or "").lower()
    if "tco" in q or "total cost of ownership" in q:
        lead = "TCO means Total Cost of Ownership."
        follow_up = "Follow-up: if you want, I can break TCO into purchase price, charging cost, maintenance, insurance, and resale assumptions."
    elif "rain" in q and any(token in q for token in ["ev", "evs", "charge", "charging", "drive", "work"]):
        lead = "Modern EVs are generally safe in rain when the vehicle and charger are in good condition."
        follow_up = "Follow-up: if you want, I can explain charging safety, flood risk, or what to check after water exposure."
    elif "limitations" in q:
        lead = "My limits are mostly about data boundaries, not EV basics."
        follow_up = "Follow-up: I can still help if you want a shortlist with clearly marked caveats."
    elif "subsid" in q:
        lead = "Subsidies are policy-sensitive, so the safe answer is to treat them as a snapshot rather than a permanent fixed number."
        follow_up = "Follow-up: tell me your state and segment if you want a grounded policy-context answer."
    else:
        lead = article.title if article else "Here is the grounded EV concept answer from the knowledge base."
        follow_up = "Follow-up: if you want, I can connect this concept back to a real EV shortlist in the dataset."

    lines = [lead]
    if article:
        support = extract_supporting_lines(article, query, limit=4)
        if support:
            lines.extend(["", "Why this matters:"])
            for item in support:
                lines.append(f"- {item}")
            lines.extend(["", f"Source: {article.title}."])

    lines.extend(
        [
            "",
            "Caveat: concept answers come from the EViq knowledge base, while model-specific decisions still depend on the current vehicle dataset.",
            "",
            follow_up,
        ]
    )
    return "\n".join(lines)
