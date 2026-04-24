from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Vehicle
import requests

router = APIRouter(prefix="/api/subsidies", tags=["Subsidies"])

# Baseline Fallback Registry
FALLBACK_STATE_SUBSIDY_MAP = {
    "karnataka": 25000,
    "maharashtra": 30000,
    "delhi": 36000,
    "gujarat": 25000,
    "tamil nadu": 20000,
    "telangana": 20000,
    "andhra pradesh": 15000,
    "arunachal pradesh": 0,
    "assam": 10000,
    "bihar": 10000,
    "chhattisgarh": 5000,
    "goa": 20000,
    "haryana": 15000,
    "himachal pradesh": 10000,
    "jharkhand": 5000,
    "kerala": 15000,
    "madhya pradesh": 10000,
    "manipur": 0,
    "meghalaya": 15000,
    "mizoram": 0,
    "nagaland": 0,
    "odisha": 15000,
    "punjab": 10000,
    "rajasthan": 15000,
    "sikkim": 0,
    "tripura": 0,
    "uttar pradesh": 20000,
    "uttarakhand": 15000,
    "west bengal": 15000,
    "andaman and nicobar": 0,
    "chandigarh": 15000,
    "dadra and nagar haveli": 0,
    "lakshadweep": 0,
    "puducherry": 0,
    "ladakh": 0,
    "jammu and kashmir": 10000,
}

POLICY_META = {
    "central_scheme": "PM E-DRIVE (indicative defaults)",
    "last_updated": "2026-04-09",
    "notes": "State subsidies change frequently; verify final dealer quotation and state transport notifications.",
    "sources": [
        "https://www.pib.gov.in/",
        "https://heavyindustries.gov.in/",
        "https://www.vahan.parivahan.gov.in/",
    ],
}

# Constants for subsidy calculations
MAX_2W_CENTRAL_SUBSIDY = 5000
PER_KWH_2W_CENTRAL_SUBSIDY = 2500
FIXED_3W_CENTRAL_SUBSIDY = 12500
TCO_COST_PER_KM_FACTOR = 0.80
TCO_FIXED_COST_5Y = 25000


# Global runtime cache for Subsidies
LIVE_SUBSIDY_CACHE = None

def get_live_state_subsidies():
    global LIVE_SUBSIDY_CACHE
    if LIVE_SUBSIDY_CACHE is not None:
        return LIVE_SUBSIDY_CACHE
        
    registry_url = "https://raw.githubusercontent.com/abhishek-4236/EV-Compare-App/main/community_subsidies.json"
    try:
        # Pinging Open Source Live Registry
        r = requests.get(registry_url, timeout=2.5)
        if r.status_code == 200:
            LIVE_SUBSIDY_CACHE = r.json()
            return LIVE_SUBSIDY_CACHE
    except Exception:
        pass
        
    LIVE_SUBSIDY_CACHE = FALLBACK_STATE_SUBSIDY_MAP
    return LIVE_SUBSIDY_CACHE

def compute_central_subsidy(vehicle: Vehicle) -> int:
    segment = str(getattr(vehicle, "segment", "") or "")
    battery_kwh = float(vehicle.battery_kwh or 0)

    # Indicative PM E-DRIVE style defaults.
    if "TWO_WHEELER" in segment:
        return int(min(MAX_2W_CENTRAL_SUBSIDY, battery_kwh * PER_KWH_2W_CENTRAL_SUBSIDY))
    if "THREE_WHEELER" in segment:
        return FIXED_3W_CENTRAL_SUBSIDY
    return 0


def compute_tco_5year(price_min: int, daily_km: int, total_subsidies: int) -> int:
    return int(
        price_min
        + (daily_km * 365 * 5 * TCO_COST_PER_KM_FACTOR)
        + TCO_FIXED_COST_5Y
        - total_subsidies
    )


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

    central_subsidy = max(int(vehicle.fame2_subsidy_inr or 0), compute_central_subsidy(vehicle))
    model_state = int(vehicle.state_subsidy_inr or 0)
    resolved_state = state.strip().lower()
    live_map = get_live_state_subsidies()
    state_bonus = int(live_map.get(resolved_state, 0))
    state_subsidy = max(model_state, state_bonus)
    total_subsidies = central_subsidy + state_subsidy
    tco_5year = compute_tco_5year(
        price_min=int(vehicle.approx_price_inr or 0),
        daily_km=daily_km,
        total_subsidies=total_subsidies,
    )

    return {
        "success": True,
        "vehicle_id": vehicle.id,
        "state": resolved_state,
        "central_subsidy_inr": central_subsidy,
        "state_subsidy_inr": state_subsidy,
        "total_applicable_subsidies": total_subsidies,
        "tco_5year_inr": tco_5year,
        "formula": "price + (daily_km * 365 * 5 * 0.80) + 25000 - total_subsidies",
        "policy_meta": POLICY_META,
    }


@router.get("/policy")
async def get_policy_snapshot():
    return {"success": True, "policy": POLICY_META, "state_defaults": get_live_state_subsidies()}
