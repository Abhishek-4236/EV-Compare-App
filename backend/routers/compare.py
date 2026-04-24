from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Vehicle
from schemas import CompareRequest

router = APIRouter(prefix="/api/compare", tags=["Compare"])

@router.post("/")
async def compare_vehicles(request: CompareRequest, db: Session = Depends(get_db)):
    if len(request.ids) < 2 or len(request.ids) > 4:
        raise HTTPException(status_code=400, detail="Send 2 to 4 vehicle IDs")

    vehicles = db.query(Vehicle).filter(Vehicle.id.in_(request.ids)).all()

    if len(vehicles) != len(request.ids):
        raise HTTPException(status_code=404, detail="One or more vehicles not found")

    # Define constants for clarity in calculations
    PRICE_NORMALIZATION_FACTOR = 10_000_000 # Used to normalize price component in value_score
    RANGE_WEIGHT = 0.35
    PRICE_WEIGHT = 0.30
    BATTERY_WEIGHT = 0.20
    RATING_WEIGHT = 0.15

    result = []
    for v in vehicles:
        price = v.approx_price_inr or 1
        range_km = v.range_km or 0
        rating = float(v.overall_rating or 3)
        battery_kwh = float(v.battery_kwh or 0)
        cost_efficiency = round(range_km / (price / 100_000), 2)
        value_score = round((range_km * RANGE_WEIGHT) +
                            ((1 / price) * PRICE_NORMALIZATION_FACTOR * PRICE_WEIGHT) +
                            (battery_kwh * BATTERY_WEIGHT) +
                            (rating * RATING_WEIGHT), 2)

        result.append({
            "id": v.id,
            "brand": v.brand,
            "model": v.model,
            "category": v.category,
            "approx_price_inr": v.approx_price_inr,
            "range_km": v.range_km,
            "battery_kwh": battery_kwh,
            "top_speed_kmh": v.top_speed_kmh,
            "charging_type": v.charging_type,
            "overall_rating": float(v.overall_rating or 0),
            "fame2_subsidy_inr": v.fame2_subsidy_inr or 0,
            "cost_efficiency": cost_efficiency,
            "value_score": value_score,
        })

    return {"success": True, "vehicles": result}
