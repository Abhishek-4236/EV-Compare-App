from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/map", tags=["Map"])

STATIC_STATIONS = [
    {"id": 1, "name": "BESCOM EV Hub", "city": "Bengaluru", "lat": 12.9716, "lng": 77.5946},
    {"id": 2, "name": "Ather Grid Koramangala", "city": "Bengaluru", "lat": 12.9352, "lng": 77.6245},
    {"id": 3, "name": "Tata Power Pune Station", "city": "Pune", "lat": 18.5204, "lng": 73.8567},
    {"id": 4, "name": "Jio-bp Charging Andheri", "city": "Mumbai", "lat": 19.1136, "lng": 72.8697},
    {"id": 5, "name": "Delhi Public EV Point", "city": "Delhi", "lat": 28.6139, "lng": 77.2090},
]


@router.get("/stations")
async def get_stations(city: str | None = Query(None)):
    if not city:
        return {"success": True, "stations": STATIC_STATIONS}

    city_norm = city.strip().lower()
    stations = [s for s in STATIC_STATIONS if s["city"].lower() == city_norm]
    return {"success": True, "stations": stations}
