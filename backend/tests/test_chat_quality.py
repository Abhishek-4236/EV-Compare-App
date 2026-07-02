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
from models import ChatFeedback, ChatMessage, ChatSession, User, Vehicle
from core.config import settings
from services.query_parser import parse_user_query


class ChatQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._original_nvidia_enabled = settings.NVIDIA_RERANK_ENABLED
        cls._original_nvidia_key = settings.NVIDIA_API_KEY
        settings.NVIDIA_RERANK_ENABLED = False
        settings.NVIDIA_API_KEY = None
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        settings.NVIDIA_RERANK_ENABLED = cls._original_nvidia_enabled
        settings.NVIDIA_API_KEY = cls._original_nvidia_key

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
        self.assertEqual(body["query_type"], "decision")
        self.assertEqual(body["user_level"], "intermediate")
        self.assertEqual(body["confidence"], "medium")
        self.assertGreaterEqual(len(body["sources"]), 3)
        prices = [item["price"] for item in body["sources"][:3]]
        self.assertEqual(prices, sorted(prices))
        names = [item["name"] for item in body["sources"][:5]]
        self.assertNotIn("Tata Xpres T EV", names)
        self.assertNotIn("Tata Ace EV pro", names)
        self.assertNotIn("Tata Ace EV 1000", names)
        for source in body["sources"][:5]:
            self.assertEqual(source["type"], "car")
            self.assertIn("matched_on", source)
        self.assertIn("Since daily usage and charging access are not specified", body["answer"])

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

    def test_identity_query_does_not_return_vehicle_sources(self):
        response = self.client.post("/api/chat/", json={"message": "who are you?"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("EViq Expert", body["answer"])
        self.assertEqual(body["sources"], [])

    def test_capabilities_query_does_not_return_vehicle_sources(self):
        response = self.client.post("/api/chat/", json={"message": "what can you do?"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("recommend", body["answer"].lower())
        self.assertEqual(body["sources"], [])

    def test_follow_up_it_can_use_assistant_vehicle_context(self):
        first = self.client.post("/api/chat/", json={"message": "Cheapest 3-wheeler EV?"})
        self.assertEqual(first.status_code, 200)
        session_id = first.json()["session_id"]

        second = self.client.post("/api/chat/", json={"message": "what are the features of it?", "session_id": session_id})
        self.assertEqual(second.status_code, 200)
        body = second.json()
        self.assertGreaterEqual(len(body["sources"]), 1)
        first_source_name = body["sources"][0]["name"]
        self.assertIn(first_source_name.split()[0], body["answer"])

    def test_difference_between_models_returns_two_sources(self):
        response = self.client.post("/api/chat/", json={"message": "difference between Ola S1 Air and Ola S1 Pro"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        names = [(item["brand"], item["model"]) for item in body["sources"][:2]]
        self.assertEqual(names, [("Ola", "S1 Air"), ("Ola", "S1 Pro")])

    def test_comparison_follow_up_table_format_keeps_same_models(self):
        first = self.client.post("/api/chat/", json={"message": "Compare Tata Nexon EV vs MG ZS EV"})
        self.assertEqual(first.status_code, 200)
        session_id = first.json()["session_id"]

        second = self.client.post("/api/chat/", json={"message": "give the comparison in table format", "session_id": session_id})
        self.assertEqual(second.status_code, 200)
        body = second.json()

        self.assertEqual(body["intent"], "comparison")
        names = [item["name"] for item in body["sources"][:2]]
        self.assertEqual(names, ["Tata Nexon EV", "MG ZS EV"])
        self.assertIn("Tata Nexon EV", body["answer"])
        self.assertIn("MG ZS EV", body["answer"])
        self.assertNotIn("Ola S1 X+", body["answer"])

    def test_vehicle_subsidy_chat_uses_tool_without_crashing(self):
        response = self.client.post(
            "/api/chat/",
            json={"message": "Tata Tiago EV price subsidy in Maharashtra for 30 km daily"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("Tata Tiago", body["answer"])
        self.assertIn("Maharashtra", body["answer"])
        self.assertIn("5-year TCO", body["answer"])

    def test_price_priority_sorts_by_lowest_price_inside_category(self):
        response = self.client.post("/api/chat/", json={"message": "cheapest scooter under 1 lakh"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["parsed_query"]["filters"]["vehicle_type"], "scooter")
        self.assertEqual(body["parsed_query"]["filters"]["priority"], "price")
        prices = [source["price"] for source in body["sources"][:3]]
        self.assertEqual(prices, sorted(prices))
        self.assertIn("Ranking basis: lowest listed price", body["answer"])

    def test_performance_priority_stays_inside_category_and_budget(self):
        response = self.client.post("/api/chat/", json={"message": "best performance car under 25 lakh"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["confidence"], "high")
        self.assertEqual(body["parsed_query"]["filters"]["priority"], "performance")
        for source in body["sources"]:
            self.assertEqual(source["type"], "car")
            self.assertLessEqual(source["price"], 2500000)
        self.assertIn("Ranking basis: performance proxy", body["answer"])

    def test_comparison_follow_up_which_is_better_reuses_recent_pair(self):
        first = self.client.post("/api/chat/", json={"message": "Compare Ather 450X vs Ola S1 Pro"})
        self.assertEqual(first.status_code, 200)
        session_id = first.json()["session_id"]

        second = self.client.post("/api/chat/", json={"message": "which one is better for value?", "session_id": session_id})
        self.assertEqual(second.status_code, 200)
        body = second.json()

        self.assertEqual(body["intent"], "comparison")
        names = [item["name"] for item in body["sources"][:2]]
        self.assertEqual(names, ["Ather 450X", "Ola S1 Pro"])

    def test_budget_correction_follow_up_keeps_previous_car_segment(self):
        first = self.client.post("/api/chat/", json={"message": "So tell me the best car under 50lakhs?"})
        self.assertEqual(first.status_code, 200)
        session_id = first.json()["session_id"]

        second = self.client.post("/api/chat/", json={"message": "Are you sure i said 20lakhs?", "session_id": session_id})
        self.assertEqual(second.status_code, 200)
        body = second.json()

        self.assertEqual(body["intent"], "recommendation")
        self.assertEqual(body["parsed_query"]["filters"]["vehicle_type"], "car")
        self.assertEqual(body["parsed_query"]["filters"]["max_price_inr"], 2000000)
        self.assertGreaterEqual(len(body["sources"]), 1)
        for source in body["sources"]:
            self.assertEqual(source["type"], "car")
            self.assertLessEqual(source["price"], 2000000)
        self.assertNotIn("Ola S1 X+", body["answer"])

    def test_chat_history_requires_session_owner(self):
        owner_email = "owner.history.security@example.com"
        other_email = "other.history.security@example.com"
        db = SessionLocal()
        try:
            users = db.query(User).filter(User.email.in_([owner_email, other_email])).all()
            user_ids = [user.id for user in users]
            if user_ids:
                session_ids = [row.id for row in db.query(ChatSession).filter(ChatSession.user_id.in_(user_ids)).all()]
                if session_ids:
                    db.query(ChatFeedback).filter(ChatFeedback.session_id.in_(session_ids)).delete(synchronize_session=False)
                    db.query(ChatMessage).filter(ChatMessage.session_id.in_(session_ids)).delete(synchronize_session=False)
                    db.query(ChatSession).filter(ChatSession.id.in_(session_ids)).delete(synchronize_session=False)
                db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
                db.commit()
        finally:
            db.close()

        owner_signup = self.client.post(
            "/api/auth/signup",
            json={"full_name": "History Owner", "email": owner_email, "password": "password123"},
        )
        self.assertEqual(owner_signup.status_code, 200)
        other_signup = self.client.post(
            "/api/auth/signup",
            json={"full_name": "History Intruder", "email": other_email, "password": "password123"},
        )
        self.assertEqual(other_signup.status_code, 200)

        owner_token = owner_signup.json()["access_token"]
        other_token = other_signup.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        other_headers = {"Authorization": f"Bearer {other_token}"}

        chat = self.client.post("/api/chat/", json={"message": "hi"}, headers=owner_headers)
        self.assertEqual(chat.status_code, 200)
        session_id = chat.json()["session_id"]

        owner_history = self.client.get(f"/api/chat/history/{session_id}", headers=owner_headers)
        self.assertEqual(owner_history.status_code, 200)
        self.assertGreaterEqual(len(owner_history.json()), 1)

        anonymous_history = self.client.get(f"/api/chat/history/{session_id}")
        self.assertEqual(anonymous_history.status_code, 401)

        other_history = self.client.get(f"/api/chat/history/{session_id}", headers=other_headers)
        self.assertEqual(other_history.status_code, 404)

        hijack_attempt = self.client.post(
            "/api/chat/",
            json={"message": "continue this chat", "session_id": session_id},
            headers=other_headers,
        )
        self.assertEqual(hijack_attempt.status_code, 404)


if __name__ == "__main__":
    unittest.main()
