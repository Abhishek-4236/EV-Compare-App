from __future__ import annotations

import re

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


def _format_advisor_answer(
    *,
    answer: str,
    why: list[str] | str,
    suggestion: str,
    optional: str | None = None,
) -> str:
    why_text = "\n".join(f"- {item}" for item in why) if isinstance(why, list) else why
    lines = [answer.strip()]
    if why_text.strip():
        lines.extend(["", why_text.strip()])
    lines.extend(["", suggestion.strip()])
    if optional:
        lines.extend(["", optional.strip()])
    return "\n".join(lines)


def _intent_label(parsed: ParsedQuery) -> str:
    if parsed.intent == "comparison":
        return "Comparison"
    if parsed.intent == "recommendation":
        return "Recommendation"
    goal = (parsed.user_goal or parsed.rewritten_query or "").lower()
    if any(token in goal for token in ["subsidy", "fame", "pm e-drive", "pm e drive", "policy", "incentive"]):
        return "Policy/Subsidy"
    if any(token in goal for token in ["tco", "total cost", "running cost", "petrol", "cost/km", "cost per km"]):
        return "Cost (TCO)"
    return "Technical"


def _extracted_context(parsed: ParsedQuery) -> list[str]:
    filters = parsed.filters
    vehicle_type = filters.vehicle_type or "not specified"
    budget = "not specified"
    if filters.min_price_inr is not None and filters.max_price_inr is not None:
        budget = f"{format_price(filters.min_price_inr)} to {format_price(filters.max_price_inr)}"
    elif filters.max_price_inr is not None:
        budget = f"up to {format_price(filters.max_price_inr)}"
    elif filters.min_price_inr is not None:
        budget = f"above {format_price(filters.min_price_inr)}"
    daily = f"{filters.daily_distance_km} km/day" if filters.daily_distance_km is not None else "not specified"
    location = filters.location or filters.state or "not specified"
    return [
        f"Budget: {budget}; daily usage: {daily}; location: {location}; vehicle type: {vehicle_type}.",
    ]


def _recommendation_assumption(parsed: ParsedQuery) -> str | None:
    filters = parsed.filters
    if (
        filters.vehicle_type
        and (filters.max_price_inr is not None or filters.min_price_inr is not None)
        and not filters.use_cases
        and filters.daily_distance_km is None
    ):
        return "Since daily usage and charging access are not specified, I ranked these by overall value within your segment and budget."
    return None


def _charging_location_guidance(parsed: ParsedQuery) -> str | None:
    filters = parsed.filters
    if filters.home_charging is False:
        return "No home charging is a real constraint, so prefer EVs with practical public/DC charging access or delay the purchase until charging is solved."
    if filters.location_tier == "tier_1":
        return "In a Tier 1 city, public charging is usually more practical, but home or workplace charging is still the best base setup."
    if filters.location_tier == "tier_2_3":
        return "In Tier 2/3 locations, prioritize dependable home charging before choosing the EV."
    return None


def _route_guidance(parsed: ParsedQuery) -> str | None:
    if {"highway", "weekend", "family"} & set(parsed.filters.use_cases):
        return "For long trips or highway use, use the route planner and check charging stops before finalizing the EV."
    return None


def build_clarification_answer(query: str, parsed: ParsedQuery) -> str:
    if parsed.intent == "comparison":
        return _format_advisor_answer(
            answer="I can compare EVs, but I need the exact two model names from the current dataset.",
            why=_extracted_context(parsed),
            suggestion="Tell me both models directly, for example: `Compare Tata Nexon EV and MG ZS EV`.",
            optional="Which two EV models should I compare?",
        )

    if parsed.intent == "recommendation":
        if parsed.filters.daily_distance_km is not None:
            return _format_advisor_answer(
                answer=f"A {parsed.filters.daily_distance_km} km daily commute is very EV-friendly, but I need one more buying anchor before recommending a model.",
                why=[
                    "Range need depends on segment, budget, and charging access.",
                    f"EV running cost is typically around ₹{parsed.filters.daily_distance_km}/day versus petrol around ₹{parsed.filters.daily_distance_km * 8}/day for this usage.",
                ],
                suggestion="Tell me your budget, whether you want a scooter/car/3-wheeler, and whether home charging is available. I can suggest the best EVs once those anchors are clear.",
                optional="What is your budget?",
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
        return _format_advisor_answer(
            answer=f"I can build a solid EV shortlist, but I still need {prompt_bits} before I make the recommendation tighter.",
            why="A useful EV recommendation depends on budget, segment, charging access, and usage.",
            suggestion=f"{ask} I can suggest the best EVs once those anchors are clear.",
            optional="What budget and vehicle type should I use?",
        )

    return _format_advisor_answer(
        answer="I need a bit more specificity to stay grounded.",
        why="I can help best when the question includes a model, budget, segment, charging need, location, or use case.",
        suggestion="Ask about a model, a comparison, a budget-based shortlist, charging, subsidies, or an EV concept like TCO.",
        optional="What EV decision do you want help with?",
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
    answer = f"{vehicle.name} is the closest grounded match in the current EViq dataset. Snapshot: {format_vehicle_snapshot(vehicle)}."
    why: list[str] = []
    if "top speed" in q:
        why.append("Top speed: unavailable in the current dataset.")
    if "warranty" in q:
        why.append("Warranty: unavailable in the current dataset.")
    if state_note:
        why.append(f"State context: {state_note}")
    return _format_advisor_answer(
        answer=answer,
        why=why,
        suggestion="If you need on-road price, dealer stock, or live subsidy, verify the latest quote.",
        optional=f"Do you want a deeper comparison against another EV in the same segment as {vehicle.name}?",
    )


def _comparison_value(value: object, fallback: str = "Unavailable") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _extract_dc_charge_time(charging_time: str | None) -> str | None:
    if not charging_time:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*(hr|hrs|hour|hours|min|mins|minute|minutes)\s*dc", charging_time, flags=re.IGNORECASE)
    if not match:
        return None
    amount = match.group(1)
    unit = match.group(2).lower()
    normalized_unit = "min" if unit.startswith("min") else "hr"
    return f"{amount} {normalized_unit}"


def _build_comparison_lead(left: VehicleDocument, right: VehicleDocument) -> str:
    if (
        left.price_inr is not None
        and right.price_inr is not None
        and left.range_km is not None
        and right.range_km is not None
    ):
        cheaper, pricier = (left, right) if left.price_inr <= right.price_inr else (right, left)
        range_gap = abs((left.range_km or 0) - (right.range_km or 0))
        if range_gap <= 20:
            return (
                f"{cheaper.name} looks like the stronger value pick, while {pricier.name} is the more premium option."
            )
    return (
        f"{left.name} and {right.name} are a trade-off, so the better pick depends on whether you care more about price, range, battery size, or charging setup."
    )


def _build_comparison_highlights(left: VehicleDocument, right: VehicleDocument) -> list[str]:
    notes: list[str] = []

    if left.price_inr is not None and right.price_inr is not None:
        cheaper, pricier = (left, right) if left.price_inr <= right.price_inr else (right, left)
        price_gap_lakh = abs(left.price_inr - right.price_inr) / 100000
        notes.append(f"Price: {cheaper.name} is lower by about ₹{price_gap_lakh:.2f} lakh.")

    if left.range_km is not None and right.range_km is not None:
        if left.range_km == right.range_km:
            notes.append(f"Range: both are listed at {left.range_km} km in the current dataset.")
        else:
            winner, loser = (left, right) if left.range_km > right.range_km else (right, left)
            range_gap = abs(left.range_km - right.range_km)
            qualifier = "slightly" if range_gap <= 20 else "clearly"
            notes.append(f"Range: {winner.name} is ahead {qualifier} by {range_gap} km.")

    if left.battery_kwh is not None and right.battery_kwh is not None and left.battery_kwh != right.battery_kwh:
        winner, loser = (left, right) if left.battery_kwh > right.battery_kwh else (right, left)
        battery_gap = abs(left.battery_kwh - right.battery_kwh)
        notes.append(f"Battery: {winner.name} has the larger pack by {battery_gap:.1f} kWh.")

    left_dc = _extract_dc_charge_time(left.charging_time)
    right_dc = _extract_dc_charge_time(right.charging_time)
    if left_dc and right_dc and left_dc == right_dc:
        notes.append(f"DC fast charging: both are listed at about {left_dc} DC, so AC charging time matters more here.")
    elif left.charging_time or right.charging_time:
        notes.append(
            f"Charging: {left.name} is listed at {_comparison_value(left.charging_time)}; {right.name} is listed at {_comparison_value(right.charging_time)}."
        )

    return notes


def build_comparison_answer(matches: list[RetrievalMatch], parsed: ParsedQuery) -> str:
    vehicles = [match.vehicle for match in matches[:2]]
    if len(vehicles) < 2:
        return _format_advisor_answer(
            answer="I can compare EVs, but I need two grounded models from the current dataset.",
            why=_extracted_context(parsed),
            suggestion="Send the exact two model names from the app dataset.",
            optional="Which two models should I compare?",
        )

    left, right = vehicles
    rows = [
        f"| Feature | {left.name} | {right.name} |",
        "|---|---|---|",
        f"| Type | {left.vehicle_type.title()} | {right.vehicle_type.title()} |",
        f"| Price | {format_price(left.price_inr)} | {format_price(right.price_inr)} |",
        f"| Range | {_comparison_value(left.range_km, 'Unavailable')} km | {_comparison_value(right.range_km, 'Unavailable')} km |",
        f"| Battery | {_comparison_value(f'{left.battery_kwh:.1f} kWh' if left.battery_kwh is not None else None)} | {_comparison_value(f'{right.battery_kwh:.1f} kWh' if right.battery_kwh is not None else None)} |",
        f"| Charging time | {_comparison_value(left.charging_time)} | {_comparison_value(right.charging_time)} |",
        f"| Charging type | {_comparison_value(left.charging_type)} | {_comparison_value(right.charging_type)} |",
    ]

    state_note = get_state_policy_note(parsed.filters.state)
    lead = _build_comparison_lead(left, right)
    highlights = _build_comparison_highlights(left, right)
    pieces = [lead, "", *rows, ""]
    if highlights:
        pieces.extend(f"- {item}" for item in highlights)
    if state_note:
        pieces.append(f"- State context: {state_note}")
    pieces.extend(
        [
            "",
            "Pick based on your main constraint: price, charging speed, highway use, or family comfort. Missing or policy-sensitive fields should still be verified before purchase.",
            "",
            "Tell me what matters most and I’ll name the better fit.",
        ]
    )
    return "\n".join(pieces)


def build_recommendation_answer(query: str, parsed: ParsedQuery, matches: list[RetrievalMatch]) -> str:
    top = matches[:3]
    q = (query or "").lower()
    if (
        parsed.filters.max_price_inr is not None
        and any(token in q for token in ["are you sure", "did i say", "i said", "meant", "actually"])
    ):
        answer = f"With the corrected budget of {format_price(parsed.filters.max_price_inr)}, I’d shortlist these EVs:"
    else:
        if parsed.filters.vehicle_type and parsed.filters.max_price_inr is not None:
            answer = f"For a {parsed.filters.vehicle_type} under {format_price(parsed.filters.max_price_inr)}, I’d shortlist these EVs:"
        elif parsed.filters.vehicle_type:
            answer = f"For a {parsed.filters.vehicle_type}, I’d shortlist these EVs:"
        else:
            answer = "I’d shortlist these EVs:"

    lines = [answer, ""]
    assumption = _recommendation_assumption(parsed)
    if assumption:
        lines.extend([assumption, ""])

    context_notes: list[str] = []
    if parsed.filters.priority:
        priority_labels = {
            "price": "lowest listed price",
            "range": "highest listed range",
            "performance": "performance proxy: range, battery size, and fast-charging support",
            "charging": "charging practicality and fast-charging support",
            "value": "overall value from listed price, range, and battery size",
        }
        context_notes.append(f"Ranking basis: {priority_labels.get(parsed.filters.priority, parsed.filters.priority)}.")

    charging_note = _charging_location_guidance(parsed)
    if charging_note:
        context_notes.append(charging_note)
    route_note = _route_guidance(parsed)
    if route_note:
        context_notes.append(route_note)
    if parsed.filters.daily_distance_km is not None:
        daily = parsed.filters.daily_distance_km
        context_notes.append(f"Running-cost estimate: EV about ₹{daily}/day versus petrol about ₹{daily * 8}/day, saving roughly ₹{daily * 7}/day at {daily} km/day.")

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
        lines.append(f"{index}. **{vehicle.name}** - {format_vehicle_snapshot(vehicle)}. Best fit: {direct_reason}.")

    if context_notes:
        lines.extend(["", *[f"- {item}" for item in context_notes]])

    state_note = get_state_policy_note(parsed.filters.state)
    if state_note:
        lines.extend(["", f"State context: {state_note}"])
        central, state_support = estimate_segment_support(top[0].vehicle, parsed.filters.state)
        if central or state_support:
            lines.append(
                f"Indicative segment support on the first option: central about ₹{central:,}, state about ₹{state_support:,}."
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
    return _format_advisor_answer(
        answer=f"I could not find a grounded match inside {joined}.",
        why="The current filters are too tight for the available EV dataset.",
        suggestion="Try relaxing one filter, or tell me which requirement matters most: budget, segment, charging, or highway range.",
    )


def build_out_of_domain_answer() -> str:
    return "Not enough data available"


def build_knowledge_answer(query: str, article: KnowledgeArticle | None) -> str:
    q = (query or "").lower()
    if any(token in q for token in ["tco", "total cost of ownership", "running cost", "petrol"]):
        lead = "TCO means Total Cost of Ownership: purchase price plus running cost, charging/fuel, maintenance, insurance, and resale."
        daily_match = re.search(r"(\d+)\s*km", q)
        savings_note = "Based on typical EV trends, EV running cost is about ₹1/km and petrol is about ₹8/km, so the saving is roughly ₹7/km."
        if daily_match:
            daily = int(daily_match.group(1))
            savings_note = f"Based on typical EV trends, at {daily} km/day the running cost is about ₹{daily}/day for an EV versus ₹{daily * 8}/day for petrol, saving roughly ₹{daily * 7}/day."
        follow_up = "Share your daily km and vehicle type if you want a simple monthly savings estimate."
    elif "rain" in q and any(token in q for token in ["ev", "evs", "charge", "charging", "drive", "work"]):
        lead = "Modern EVs are generally safe in rain when the vehicle and charger are in good condition."
        savings_note = None
        follow_up = "I can explain charging safety, flood risk, or what to check after water exposure."
    elif "limitations" in q:
        lead = "My limits are mostly about data boundaries, not EV basics."
        savings_note = None
        follow_up = "I can still help with a shortlist and clearly marked caveats."
    elif "subsid" in q:
        lead = "Subsidies are policy-sensitive, so the safe answer is to treat them as a snapshot rather than a permanent fixed number."
        savings_note = None
        follow_up = "Tell me your state and segment if you want a grounded policy-context answer."
    else:
        lead = article.title if article else "Here is the grounded EV concept answer from the knowledge base."
        savings_note = None
        follow_up = "I can connect this concept back to a real EV shortlist in the dataset."

    why: list[str] = []
    if savings_note:
        why.append(savings_note)
    if article:
        support = extract_supporting_lines(article, query, limit=4)
        if support:
            why.extend(support)
        why.append(f"Source: {article.title}.")

    return _format_advisor_answer(
        answer=lead,
        why=why,
        suggestion="Use this as guidance from the EViq knowledge base; model-specific decisions still depend on the current vehicle dataset.",
        optional=follow_up,
    )
