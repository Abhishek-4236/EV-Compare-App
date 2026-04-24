import json
import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient

from main import app
from services.chat_analysis import build_query_plan, normalize_query_text
from services.retrieval import station_answer
from database import SessionLocal
from models import Vehicle
from services.query_parser import parse_user_query


class ChatQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_list_all_evs_is_inventory_not_compare(self):
        db = SessionLocal()
        try:
            plan = build_query_plan("list all EVs", db)
        finally:
            db.close()
        self.assertEqual(plan.intent, "inventory")
        self.assertFalse(plan.needs_clarification)

    def test_regen_braking_is_knowledge_query(self):
        db = SessionLocal()
        try:
            plan = build_query_plan("what is regen braking", db)
        finally:
            db.close()
        self.assertEqual(plan.intent, "knowledge")

    def test_query_normalization_handles_common_typos(self):
        normalized = normalize_query_text("best electic scooty under 1 lakh with good battary")
        self.assertIn("electric", normalized)
        self.assertIn("scooter", normalized)
        self.assertIn("battery", normalized)

    def test_lfp_vs_nmc_is_concept_compare(self):
        db = SessionLocal()
        try:
            plan = build_query_plan("compare LFP vs NMC for Indian heat", db)
        finally:
            db.close()
        self.assertEqual(plan.intent, "concept_compare")
        self.assertFalse(plan.needs_clarification)

    def test_vehicle_compare_detects_real_models(self):
        db = SessionLocal()
        try:
            plan = build_query_plan("compare Ola S1 Pro vs Ather 450X", db)
        finally:
            db.close()
        self.assertEqual(plan.intent, "vehicle_compare")
        self.assertGreaterEqual(len(plan.compare_targets), 2)

    def test_station_answer_does_not_hallucinate_other_city(self):
        answer = station_answer("any charging station near Hyderabad")
        self.assertIn("Hyderabad", answer)
        self.assertNotIn("Bengaluru", answer)
        self.assertNotIn("Pune", answer)

    def test_inventory_route_returns_summary(self):
        response = self.client.post("/api/chat/", json={"message": "list all EVs"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("We have", body["answer"])
        self.assertNotIn("Please share two EV model", body["answer"])

    def test_browse_cars_excludes_commercial_4w_entries(self):
        response = self.client.get("/api/vehicles/?category=4W&limit=100")
        self.assertEqual(response.status_code, 200)
        vehicles = response.json()["vehicles"]
        self.assertGreater(len(vehicles), 0)
        for vehicle in vehicles:
            vehicle_type = (vehicle.get("vehicle_type") or "").lower()
            self.assertFalse(any(token in vehicle_type for token in ["commercial", "cargo", "truck", "mini truck", "scv"]))

    def test_recommend_scooter_returns_results(self):
        response = self.client.post(
            "/api/recommend/",
            json={"budget": 120000, "daily_km": 35, "segment": "scooter", "priority": "price"},
        )
        self.assertEqual(response.status_code, 200)
        recommendations = response.json()["recommendations"]
        self.assertGreater(len(recommendations), 0)
        for item in recommendations:
            self.assertGreater(item["id"], 0)

    def test_recommend_auto_maps_to_three_wheeler(self):
        response = self.client.post(
            "/api/recommend/",
            json={"budget": 600000, "daily_km": 50, "segment": "auto", "priority": "price"},
        )
        self.assertEqual(response.status_code, 200)
        recommendations = response.json()["recommendations"]
        self.assertGreater(len(recommendations), 0)
        db = SessionLocal()
        try:
            categories = {
                db.query(Vehicle).filter(Vehicle.id == item["id"]).first().category
                for item in recommendations
            }
            self.assertEqual(categories, {"3W"})
        finally:
            db.close()

    def test_pronoun_follow_up_uses_previous_vehicle(self):
        first = self.client.post("/api/chat/", json={"message": "Ola S1 Pro price and battery"})
        self.assertEqual(first.status_code, 200)
        session_id = first.json()["session_id"]

        second = self.client.post("/api/chat/", json={"message": "and its top speed?", "session_id": session_id})
        self.assertEqual(second.status_code, 200)
        answer = second.json()["answer"]
        self.assertIn("Ola S1 Pro", answer)
        self.assertIn("Top speed", answer)

    def test_stream_and_non_stream_match_for_inventory(self):
        normal = self.client.post("/api/chat/", json={"message": "list all EVs"})
        self.assertEqual(normal.status_code, 200)
        expected = normal.json()["answer"].strip()

        stream = self.client.post("/api/chat/stream", json={"message": "list all EVs"})
        self.assertEqual(stream.status_code, 200)
        chunks = []
        for raw_line in stream.text.splitlines():
            if not raw_line.startswith("data: "):
                continue
            payload = json.loads(raw_line[6:])
            if payload.get("type") == "chunk":
                chunks.append(payload["content"])
        streamed_answer = "".join(chunks).strip()
        self.assertEqual(streamed_answer, expected)

    def test_budget_car_query_returns_only_cars_with_multiple_matches(self):
        response = self.client.post("/api/chat/", json={"message": "Show EV cars under 15 lakh"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["intent"], "recommendation")
        self.assertGreaterEqual(len(body["sources"]), 3)
        prices = [item["price"] for item in body["sources"][:3]]
        self.assertEqual(prices, sorted(prices))
        names = [item["name"] for item in body["sources"][:5]]
        self.assertNotIn("Tata Xpres T EV", names)
        self.assertNotIn("Tata Ace EV pro", names)
        self.assertNotIn("Tata Ace EV 1000", names)
        for source in body["sources"][:5]:
            self.assertEqual(source["type"], "car")

    def test_cheapest_three_wheeler_is_sorted_by_price(self):
        response = self.client.post("/api/chat/", json={"message": "Cheapest 3-wheeler EV?"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["intent"], "recommendation")
        prices = [item["price"] for item in body["sources"][:3]]
        self.assertEqual(prices, sorted(prices))

    def test_query_parser_does_not_treat_evs_as_comparison_marker(self):
        parsed = parse_user_query("can EVs work in rain?")
        self.assertEqual(parsed.intent, "info")

    def test_location_query_returns_location_text_not_vehicle_matches(self):
        response = self.client.post("/api/chat/", json={"message": "charging stations near Bengaluru"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("charging locations", body["answer"].lower())
        self.assertEqual(body["sources"], [])

    def test_difference_between_models_returns_two_sources(self):
        response = self.client.post("/api/chat/", json={"message": "difference between Ola S1 Air and Ola S1 Pro"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        names = [(item["brand"], item["model"]) for item in body["sources"][:2]]
        self.assertEqual(names, [("Ola", "S1 Air"), ("Ola", "S1 Pro")])


if __name__ == "__main__":
    unittest.main()
