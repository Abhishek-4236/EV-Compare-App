from math import asin, cos, radians, sin, sqrt

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/map", tags=["Map"])

STATIC_STATIONS = [
    {"id": 1, "name": "BESCOM EV Hub", "city": "Bengaluru", "lat": 12.9716, "lng": 77.5946, "power_kw": 30, "connector": "CCS2/Type 2"},
    {"id": 2, "name": "Ather Grid Koramangala", "city": "Bengaluru", "lat": 12.9352, "lng": 77.6245, "power_kw": 15, "connector": "Type 2"},
    {"id": 3, "name": "Tata Power Pune Station", "city": "Pune", "lat": 18.5204, "lng": 73.8567, "power_kw": 30, "connector": "CCS2"},
    {"id": 4, "name": "Jio-bp Charging Andheri", "city": "Mumbai", "lat": 19.1136, "lng": 72.8697, "power_kw": 60, "connector": "CCS2"},
    {"id": 5, "name": "Delhi Public EV Point", "city": "Delhi", "lat": 28.6139, "lng": 77.2090, "power_kw": 50, "connector": "CCS2"},
    {"id": 6, "name": "Jaipur Highway Charging Plaza", "city": "Jaipur", "lat": 26.9124, "lng": 75.7873, "power_kw": 30, "connector": "CCS2"},
    {"id": 7, "name": "Ahmedabad DC Fast Hub", "city": "Ahmedabad", "lat": 23.0225, "lng": 72.5714, "power_kw": 60, "connector": "CCS2"},
    {"id": 8, "name": "Hyderabad HITEC EV Point", "city": "Hyderabad", "lat": 17.4435, "lng": 78.3772, "power_kw": 30, "connector": "CCS2/Type 2"},
    {"id": 9, "name": "Chennai OMR Charging Hub", "city": "Chennai", "lat": 12.9165, "lng": 80.2302, "power_kw": 50, "connector": "CCS2"},
    {"id": 10, "name": "Kochi Mobility Charging", "city": "Kochi", "lat": 9.9312, "lng": 76.2673, "power_kw": 25, "connector": "CCS2/Type 2"},
]

CITY_COORDS = {
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "kochi": (9.9312, 76.2673),
}


class RoutePlanRequest(BaseModel):
    source: str = Field(..., min_length=2)
    destination: str = Field(..., min_length=2)
    range_km: int = Field(250, ge=50, le=900)
    start_soc_percent: int = Field(90, ge=10, le=100)
    reserve_percent: int = Field(15, ge=5, le=40)


def haversine_km(left_lat: float, left_lng: float, right_lat: float, right_lng: float) -> float:
    radius_km = 6371.0
    dlat = radians(right_lat - left_lat)
    dlng = radians(right_lng - left_lng)
    a = sin(dlat / 2) ** 2 + cos(radians(left_lat)) * cos(radians(right_lat)) * sin(dlng / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def resolve_city(name: str) -> tuple[float, float]:
    key = name.strip().lower()
    if key not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"Unsupported city '{name}'. Try Delhi, Mumbai, Bengaluru, Pune, Hyderabad, Chennai, Ahmedabad, Jaipur, Lucknow, or Kochi.")
    return CITY_COORDS[key]


def distance_to_segment_km(station: dict, start: tuple[float, float], end: tuple[float, float]) -> float:
    # Lightweight approximation: if total start-station-end is close to route distance,
    # the station is near the corridor.
    route = haversine_km(start[0], start[1], end[0], end[1])
    via_station = haversine_km(start[0], start[1], station["lat"], station["lng"]) + haversine_km(station["lat"], station["lng"], end[0], end[1])
    return max(0.0, via_station - route)


@router.get("/stations")
async def get_stations(city: str | None = Query(None)):
    if not city:
        return {"success": True, "stations": STATIC_STATIONS}

    city_norm = city.strip().lower()
    stations = [s for s in STATIC_STATIONS if s["city"].lower() == city_norm]
    return {"success": True, "stations": stations}


@router.post("/route-plan")
async def route_plan(request: RoutePlanRequest):
    source = resolve_city(request.source)
    destination = resolve_city(request.destination)
    route_distance = round(haversine_km(source[0], source[1], destination[0], destination[1]) * 1.18, 1)
    usable_range = max(1, request.range_km * ((request.start_soc_percent - request.reserve_percent) / 100))
    charging_needed = route_distance > usable_range

    corridor_stations = []
    for station in STATIC_STATIONS:
        route_detour = distance_to_segment_km(station, source, destination)
        if route_detour <= 120:
            distance_from_source = haversine_km(source[0], source[1], station["lat"], station["lng"]) * 1.18
            corridor_stations.append({**station, "distance_from_source_km": round(distance_from_source, 1), "route_detour_score_km": round(route_detour, 1)})

    corridor_stations.sort(key=lambda item: (item["distance_from_source_km"], -item.get("power_kw", 0)))

    recommended_stops = []
    if charging_needed:
        last_stop_km = 0.0
        max_leg = request.range_km * ((100 - request.reserve_percent) / 100)
        for station in corridor_stations:
            leg = station["distance_from_source_km"] - last_stop_km
            remaining_after_station = route_distance - station["distance_from_source_km"]
            if leg <= max_leg and remaining_after_station > usable_range * 0.55:
                recommended_stops.append(station)
                last_stop_km = station["distance_from_source_km"]
            if route_distance - last_stop_km <= max_leg:
                break

    return {
        "success": True,
        "route": {
            "source": request.source,
            "destination": request.destination,
            "source_coords": {"lat": source[0], "lng": source[1]},
            "destination_coords": {"lat": destination[0], "lng": destination[1]},
            "estimated_distance_km": route_distance,
            "usable_range_km": round(usable_range, 1),
            "charging_needed": charging_needed,
            "polyline": [
                {"lat": source[0], "lng": source[1]},
                *[{"lat": station["lat"], "lng": station["lng"]} for station in recommended_stops],
                {"lat": destination[0], "lng": destination[1]},
            ],
        },
        "recommended_stops": recommended_stops[:4],
        "stations_along_route": corridor_stations[:8],
        "note": "Route distance is a local estimate using bundled Indian city and charging station data. Use a live map app for final navigation.",
    }
