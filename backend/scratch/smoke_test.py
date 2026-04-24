import requests
import time

BASE_URL = "http://localhost:8000"

def test_endpoints():
    print("--- Starting Backend Smoke Test ---")
    
    # 1. Vehicles List
    try:
        r = requests.get(f"{BASE_URL}/api/vehicles/?limit=5")
        print(f"[FETCH] /api/vehicles/ -> {r.status_code}")
        if r.status_code == 200:
            print(f"       Count: {len(r.json().get('vehicles', []))}")
    except Exception as e:
        print(f"[FAIL] /api/vehicles/ -> {e}")

    # 2. Map Stations
    try:
        r = requests.get(f"{BASE_URL}/api/map/stations?lat=12.9716&lon=77.5946") # Bangalore
        print(f"[FETCH] /api/map/stations -> {r.status_code}")
        if r.status_code == 200:
            print(f"       Stations found: {len(r.json())}")
    except Exception as e:
        print(f"[FAIL] /api/map/stations -> {e}")

    # 3. Chat (Non-streaming check)
    try:
        # We'll use a simple query that should return quickly
        payload = {"message": "Hello", "session_id": "test-session-123"}
        r = requests.post(f"{BASE_URL}/api/chat/", json=payload)
        print(f"[POST] /api/chat/ -> {r.status_code}")
        if r.status_code == 200:
            print(f"       Response length: {len(r.text)}")
    except Exception as e:
        print(f"[FAIL] /api/chat/ -> {e}")

    # 4. Subsidy Calculator
    try:
        # Find a vehicle ID first
        vid_res = requests.get(f"{BASE_URL}/api/vehicles/?limit=1").json()
        vid = vid_res.get('vehicles', [])[0]['id']
        r = requests.get(f"{BASE_URL}/api/subsidies/?vehicle_id={vid}&state=karnataka")
        print(f"[FETCH] /api/subsidies/ -> {r.status_code}")
    except Exception as e:
        print(f"[FAIL] /api/subsidies/calculate -> {e}")

    print("--- Smoke Test Complete ---")

if __name__ == "__main__":
    test_endpoints()
