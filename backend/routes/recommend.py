from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import not_, or_
from database import get_db
from models import Vehicle
from schemas import RecommendRequest

router = APIRouter(prefix="/api/recommend", tags=["Recommend"])


def passenger_car_filter():
    commercial_like = or_(
        Vehicle.vehicle_type.ilike("%commercial%"),
        Vehicle.vehicle_type.ilike("%cargo%"),
        Vehicle.vehicle_type.ilike("%truck%"),
        Vehicle.vehicle_type.ilike("%mini truck%"),
        Vehicle.vehicle_type.ilike("%scv%"),
        Vehicle.vehicle_type.ilike("%delivery%"),
    )
    return or_(Vehicle.vehicle_type.is_(None), not_(commercial_like))

@router.post("/")
async def recommend_vehicles(request: RecommendRequest, db: Session = Depends(get_db)):
    required_range = int(request.daily_km * 1.3)

    query = db.query(Vehicle).filter(
        Vehicle.approx_price_inr <= request.budget,
        Vehicle.range_km >= required_range,
        Vehicle.market_status == "Available"
    )

    seg = request.segment.lower()
    if seg == "scooter":
        query = query.filter(
            Vehicle.category == "2W",
            Vehicle.vehicle_type.ilike("%scooter%")
        )
    elif seg in {"motorcycle", "bike"}:
        query = query.filter(
            Vehicle.category == "2W",
            or_(
                Vehicle.vehicle_type.ilike("%motorcycle%"),
                Vehicle.vehicle_type.ilike("%bike%"),
            )
        )
    elif seg == "car":
        query = query.filter(Vehicle.category == "4W", passenger_car_filter())
    elif seg in {"auto", "three_wheeler", "3w"}:
        query = query.filter(Vehicle.category == "3W")
    elif seg == "truck":
        query = query.filter(Vehicle.category == "Truck")

    vehicles = query.limit(30).all()
    priority = request.priority.lower()

    if priority == "range":
        weights = {"range": 0.50, "price": 0.25, "speed": 0.25}
    elif priority == "price":
        weights = {"range": 0.25, "price": 0.50, "speed": 0.25}
    elif priority == "speed":
        weights = {"range": 0.25, "price": 0.25, "speed": 0.50}
    else:
        weights = {"range": 1 / 3, "price": 1 / 3, "speed": 1 / 3}

    scored = []
    for v in vehicles:
        price = float(v.approx_price_inr or 1)
        range_km = float(v.range_km or 0)
        speed = float(v.top_speed_kmh or 0)
        battery_kwh = float(v.battery_kwh or 0)
        rating = float(v.overall_rating or 3)

        # Required VALUE_SCORE formula.
        value_score = round(
            (range_km * 0.35)
            + ((1 / price) * 10000000 * 0.30)
            + (battery_kwh * 0.20)
            + (rating * 0.15),
            2,
        )

        recommend_score = (
            (range_km * weights["range"])
            + (((1 / price) * 10000000) * weights["price"])
            + (speed * weights["speed"])
        )
        scored.append((v, round(recommend_score, 2), value_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top_results = scored[:5]

    return {
        "success": True,
        "query": {
            "budget": request.budget,
            "daily_km": request.daily_km,
            "required_range": required_range,
            "segment": request.segment
        },
        "recommendations": [
            {
                "id": v.id,
                "brand": v.brand,
                "model": v.model,
                "approx_price_inr": v.approx_price_inr,
                "range_km": v.range_km,
                "battery_kwh": float(v.battery_kwh),
                "overall_rating": float(v.overall_rating or 0),
                "fame2_subsidy_inr": v.fame2_subsidy_inr or 0,
                "effective_price": v.approx_price_inr - (v.fame2_subsidy_inr or 0),
                "recommend_score": score,
                "value_score": value_score,
            }
            for v, score, value_score in top_results
        ]
    }
