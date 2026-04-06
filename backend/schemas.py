from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class VehicleOut(BaseModel):
    id: int
    category: str
    wheel_type: Optional[str] = None
    brand: str
    model: str
    approx_price_inr: int
    range_km: int
    battery_kwh: Decimal
    top_speed_kmh: Optional[int] = None
    motor_kw: Optional[Decimal] = None
    charging_time_ac_hrs: Optional[Decimal] = None
    charging_time_dc_min: Optional[int] = None
    monthly_cost_inr: Optional[int] = None
    safety_rating: Optional[int] = None
    brake_type: Optional[str] = None
    fame2_subsidy_inr: Optional[int] = 0
    overall_rating: Optional[Decimal] = None
    charging_type: Optional[str] = None
    vehicle_type: Optional[str] = None
    market_status: Optional[str] = None
    launch_year: Optional[int] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class VehicleListResponse(BaseModel):
    success: bool
    total: int
    page: int
    vehicles: list[VehicleOut]


class CompareRequest(BaseModel):
    ids: list[int]


class RecommendRequest(BaseModel):
    budget: int
    daily_km: int
    segment: str
    priority: str