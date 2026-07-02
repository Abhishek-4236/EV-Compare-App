from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import not_, or_
from sqlalchemy.orm import Session

from models import Vehicle
from services.subsidy_service import build_subsidy_snapshot


@dataclass(frozen=True)
class ToolResult:
    tool: str
    ok: bool
    data: dict[str, Any]


def _passenger_car_filter():
    commercial_like = or_(
        Vehicle.vehicle_type.ilike("%commercial%"),
        Vehicle.vehicle_type.ilike("%cargo%"),
        Vehicle.vehicle_type.ilike("%truck%"),
        Vehicle.vehicle_type.ilike("%mini truck%"),
        Vehicle.vehicle_type.ilike("%scv%"),
        Vehicle.vehicle_type.ilike("%delivery%"),
    )
    return or_(Vehicle.vehicle_type.is_(None), not_(commercial_like))


def tool_get_vehicles(
    db: Session,
    *,
    category: str | None = None,
    brand: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    min_range: int | None = None,
    max_range: int | None = None,
    charging_type: str | None = None,
    sort_by: Literal["approx_price_inr", "range_km", "overall_rating", "battery_kwh", "top_speed_kmh"] = "overall_rating",
    sort_order: Literal["ASC", "DESC"] = "DESC",
    page: int = 1,
    limit: int = 20,
) -> ToolResult:
    query = db.query(Vehicle).filter(Vehicle.market_status == "Available")

    if category:
        query = query.filter(Vehicle.category == category)
        if category == "4W":
            query = query.filter(_passenger_car_filter())
    if brand:
        query = query.filter(Vehicle.brand == brand)
    if min_price:
        query = query.filter(Vehicle.approx_price_inr >= min_price)
    if max_price:
        query = query.filter(Vehicle.approx_price_inr <= max_price)
    if min_range:
        query = query.filter(Vehicle.range_km >= min_range)
    if max_range:
        query = query.filter(Vehicle.range_km <= max_range)
    if charging_type:
        query = query.filter(Vehicle.charging_type == charging_type)

    total = int(query.count())
    sort_col = getattr(Vehicle, sort_by)
    query = query.order_by(sort_col.desc() if sort_order == "DESC" else sort_col.asc())

    vehicles = query.offset((page - 1) * limit).limit(limit).all()
    payload = [
        {
            "id": v.id,
            "segment": str(v.segment),
            "category": v.category,
            "brand": v.brand,
            "model": v.model,
            "name": f"{v.brand} {v.model}".strip(),
            "approx_price_inr": v.approx_price_inr,
            "range_km": v.range_km,
            "battery_kwh": float(v.battery_kwh or 0),
            "top_speed_kmh": v.top_speed_kmh,
            "charging_type": v.charging_type,
            "vehicle_type": v.vehicle_type,
            "overall_rating": float(v.overall_rating or 0),
            "fame2_subsidy_inr": int(v.fame2_subsidy_inr or 0),
            "state_subsidy_inr": int(v.state_subsidy_inr or 0),
        }
        for v in vehicles
    ]
    return ToolResult(
        tool="get_vehicles",
        ok=True,
        data={"success": True, "total": total, "page": page, "vehicles": payload},
    )


def tool_compare_vehicles(db: Session, *, ids: list[int]) -> ToolResult:
    if len(ids) < 2 or len(ids) > 4:
        return ToolResult(
            tool="compare_vehicles",
            ok=False,
            data={"success": False, "detail": "Send 2 to 4 vehicle IDs"},
        )

    vehicles = db.query(Vehicle).filter(Vehicle.id.in_(ids)).all()
    if len(vehicles) != len(ids):
        return ToolResult(
            tool="compare_vehicles",
            ok=False,
            data={"success": False, "detail": "One or more vehicles not found"},
        )

    PRICE_NORMALIZATION_FACTOR = 10_000_000
    RANGE_WEIGHT = 0.35
    PRICE_WEIGHT = 0.30
    BATTERY_WEIGHT = 0.20
    RATING_WEIGHT = 0.15

    result: list[dict[str, Any]] = []
    for v in vehicles:
        price = int(v.approx_price_inr or 1)
        range_km = int(v.range_km or 0)
        rating = float(v.overall_rating or 3)
        battery_kwh = float(v.battery_kwh or 0)

        cost_efficiency = round(range_km / (price / 100_000), 2)
        value_score = round(
            (range_km * RANGE_WEIGHT)
            + ((1 / price) * PRICE_NORMALIZATION_FACTOR * PRICE_WEIGHT)
            + (battery_kwh * BATTERY_WEIGHT)
            + (rating * RATING_WEIGHT),
            2,
        )

        result.append(
            {
                "id": v.id,
                "brand": v.brand,
                "model": v.model,
                "name": f"{v.brand} {v.model}".strip(),
                "category": v.category,
                "approx_price_inr": v.approx_price_inr,
                "range_km": v.range_km,
                "battery_kwh": battery_kwh,
                "top_speed_kmh": v.top_speed_kmh,
                "charging_type": v.charging_type,
                "overall_rating": float(v.overall_rating or 0),
                "fame2_subsidy_inr": int(v.fame2_subsidy_inr or 0),
                "state_subsidy_inr": int(v.state_subsidy_inr or 0),
                "cost_efficiency": cost_efficiency,
                "value_score": value_score,
            }
        )

    return ToolResult(tool="compare_vehicles", ok=True, data={"success": True, "vehicles": result})


def tool_get_subsidies(db: Session, *, vehicle_id: int, state: str, daily_km: int = 30) -> ToolResult:
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        return ToolResult(
            tool="get_subsidies",
            ok=False,
            data={"success": False, "detail": "Vehicle not found"},
        )

    return ToolResult(
        tool="get_subsidies",
        ok=True,
        data=build_subsidy_snapshot(vehicle, state=state, daily_km=int(daily_km)),
    )

