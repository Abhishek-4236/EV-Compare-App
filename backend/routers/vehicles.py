from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import Vehicle
from schemas import VehicleOut, VehicleListResponse

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])

ALLOWED_SORTS = [
    "approx_price_inr", "range_km",
    "overall_rating", "battery_kwh", "top_speed_kmh"
]

@router.get("/meta/brands")
def get_brands(db: Session = Depends(get_db)):
    brands = db.query(Vehicle.brand).distinct().order_by(Vehicle.brand).all()
    return {"brands": [b[0] for b in brands]}


@router.get("/", response_model=VehicleListResponse)
def get_vehicles(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_range: Optional[int] = None,
    max_range: Optional[int] = None,
    charging_type: Optional[str] = None,
    sort_by: str = "overall_rating",
    sort_order: str = "DESC",
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(Vehicle).filter(Vehicle.market_status == "Available")

    if category:
        query = query.filter(Vehicle.category == category)
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

    total = query.count()

    safe_sort = sort_by if sort_by in ALLOWED_SORTS else "overall_rating"
    sort_col = getattr(Vehicle, safe_sort)
    query = query.order_by(
        sort_col.desc() if sort_order == "DESC" else sort_col.asc()
    )

    vehicles = query.offset((page - 1) * limit).limit(limit).all()

    return VehicleListResponse(
        success=True, total=total, page=page, vehicles=vehicles
    )


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle