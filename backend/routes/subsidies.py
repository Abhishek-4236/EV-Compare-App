from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Vehicle
from services.subsidy_service import (
    POLICY_META,
    build_subsidy_snapshot,
    get_live_state_subsidies,
)

router = APIRouter(prefix="/api/subsidies", tags=["Subsidies"])


@router.get("/")
async def get_subsidies(
    vehicle_id: int = Query(..., gt=0),
    state: str = Query("karnataka"),
    daily_km: int = Query(30, gt=0, le=500),
    db: Session = Depends(get_db),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    return build_subsidy_snapshot(vehicle, state=state, daily_km=daily_km)


@router.get("/policy")
async def get_policy_snapshot():
    return {"success": True, "policy": POLICY_META, "state_defaults": get_live_state_subsidies()}
