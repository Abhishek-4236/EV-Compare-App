from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Vehicle
from schemas import CompareRequest

router = APIRouter(prefix="/api/compare", tags=["Compare"])

@router.post("/")
def compare_vehicles(request: CompareRequest, db: Session = Depends(get_db)):
    if len(request.ids) < 2 or len(request.ids) > 3:
        raise HTTPException(status_code=400, detail="Send 2 or 3 vehicle IDs")

    vehicles = db.query(Vehicle).filter(Vehicle.id.in_(request.ids)).all()

    if len(vehicles) != len(request.ids):
        raise HTTPException(status_code=404, detail="One or more vehicles not found")

    result = []
    for v in vehicles:
        price = v.approx_price_inr or 1
        range_km = v.range_km or 0
        rating = float(v.overall_rating or 3)

        cost_efficiency = round(range_km / (price / 100000), 2)
        value_score = round(
            (max(0, 100 - price / 100000) * 0.4) +
            (min(range_km / 5, 100) * 0.4) +
            (rating * 20 * 0.2)
        )

        result.append({
            "id": v.id,
            "brand": v.brand,
            "model": v.model,
            "category": v.category,
            "approx_price_inr": v.approx_price_inr,
            "range_km": v.range_km,
            "battery_kwh": float(v.battery_kwh),
            "top_speed_kmh": v.top_speed_kmh,
            "charging_type": v.charging_type,
            "overall_rating": float(v.overall_rating or 0),
            "fame2_subsidy_inr": v.fame2_subsidy_inr or 0,
            "cost_efficiency": cost_efficiency,
            "value_score": value_score,
        })

    return {"success": True, "vehicles": result}