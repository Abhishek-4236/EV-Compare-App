from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Vehicle
from schemas import RecommendRequest

router = APIRouter(prefix="/api/recommend", tags=["Recommend"])

@router.post("/")
def recommend_vehicles(request: RecommendRequest, db: Session = Depends(get_db)):
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
            Vehicle.wheel_type.ilike("%scooter%")
        )
    elif seg == "motorcycle":
        query = query.filter(
            Vehicle.category == "2W",
            Vehicle.wheel_type.ilike("%motorcycle%")
        )
    elif seg == "car":
        query = query.filter(Vehicle.category == "4W")
    elif seg == "truck":
        query = query.filter(Vehicle.category == "Truck")

    priority = request.priority.lower()
    if priority == "range":
        query = query.order_by(Vehicle.range_km.desc())
    elif priority == "speed":
        query = query.order_by(Vehicle.top_speed_kmh.desc())
    elif priority == "features":
        query = query.order_by(Vehicle.overall_rating.desc())
    else:
        query = query.order_by(Vehicle.approx_price_inr.asc())

    vehicles = query.limit(5).all()

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
                "effective_price": v.approx_price_inr - (v.fame2_subsidy_inr or 0)
            }
            for v in vehicles
        ]
    }