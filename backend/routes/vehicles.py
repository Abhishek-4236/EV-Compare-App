from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import not_, or_
from typing import Optional, Literal
from database import get_db
from models import Vehicle
from schemas import VehicleOut, VehicleListResponse, FeaturedDiverseResponse

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])


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
    sort_by: Literal["approx_price_inr", "range_km", "overall_rating", "battery_kwh", "top_speed_kmh"] = "overall_rating",
    sort_order: Literal["ASC", "DESC"] = "DESC",
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(Vehicle).filter(Vehicle.market_status == "Available")

    if category:
        query = query.filter(Vehicle.category == category)
        if category == "4W":
            query = query.filter(passenger_car_filter())
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

    safe_sort = sort_by # Type hinting now ensures it's safe
    sort_col = getattr(Vehicle, safe_sort)
    query = query.order_by(
        sort_col.desc() if sort_order == "DESC" else sort_col.asc()
    )

    vehicles = query.offset((page - 1) * limit).limit(limit).all()

    return VehicleListResponse(
        success=True, total=total, page=page, vehicles=vehicles
    )



@router.get("/featured/diverse", response_model=FeaturedDiverseResponse)
def get_featured_diverse(db: Session = Depends(get_db)):
    """
    Returns one top-rated vehicle for each major configuration: 
    Bike, Scooter, Car, 3-Wheeler, Bus, Truck
    """
    results = []

    # 1. Motorcycle (Bike)
    bike = db.query(Vehicle).filter(Vehicle.category == "2W", Vehicle.vehicle_type == "Motorcycle").order_by(Vehicle.overall_rating.desc()).first()
    if bike: results.append(bike)

    # 2. Scooter
    scooter = db.query(Vehicle).filter(Vehicle.category == "2W", Vehicle.vehicle_type.ilike("scooter")).order_by(Vehicle.overall_rating.desc()).first()
    if scooter: results.append(scooter)

    # 3. Car (4W)
    car = db.query(Vehicle).filter(Vehicle.category == "4W", passenger_car_filter()).order_by(Vehicle.overall_rating.desc()).first()
    if car: results.append(car)

    # 4. 3-Wheeler (3W)
    three_w = db.query(Vehicle).filter(Vehicle.category == "3W").order_by(Vehicle.overall_rating.desc()).first()
    if three_w: results.append(three_w)

    # 5. Bus
    bus = db.query(Vehicle).filter(Vehicle.category == "Bus").order_by(Vehicle.overall_rating.desc()).first()
    if bus: results.append(bus)

    # 6. Truck
    truck = db.query(Vehicle).filter(Vehicle.category == "Truck").order_by(Vehicle.overall_rating.desc()).first()
    if truck: results.append(truck)

    return {"success": True, "vehicles": results}


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle
