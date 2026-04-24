import unittest
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.config import settings
from services.ev_catalog import build_vehicle_text, load_excel_as_documents
from services.ev_rag import EVRAGService
from services.ev_rag_types import ParsedQuery
from services.faiss_store import FaissStore
from services.query_parser import parse_user_query

try:
    __import__("faiss")
    HAS_FAISS = True
except Exception:
    HAS_FAISS = False


class EVRAGPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rag = EVRAGService()

    def test_excel_is_normalized_into_documents(self):
        documents = load_excel_as_documents(settings.EV_EXCEL_PATH)
        self.assertGreater(len(documents), 0)
        self.assertTrue(documents[0].id)
        self.assertTrue(documents[0].name)
        self.assertIsInstance(documents[0].features, list)

    def test_vehicle_text_builder_includes_core_fields(self):
        document = load_excel_as_documents(settings.EV_EXCEL_PATH)[0]
        text = build_vehicle_text(document)
        self.assertIn(document.name, text)
        self.assertIn("Price:", text)
        self.assertIn("Range:", text)

    @unittest.skipUnless(HAS_FAISS, "faiss-cpu is not installed in this environment")
    def test_faiss_store_returns_results(self):
        vectors = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.9, 0.1, 0.0],
        ]
        store = FaissStore.build(vectors=vectors, ids=["a", "b", "c"])
        results = store.search([1.0, 0.0, 0.0], top_k=2)
        self.assertEqual(results[0][0], "a")
        self.assertEqual(len(results), 2)

    def test_parser_falls_back_to_heuristics(self):
        parsed = parse_user_query("best electric bike under 2 lakh with 150 km range")
        self.assertIsInstance(parsed, ParsedQuery)
        self.assertEqual(parsed.intent, "recommendation")
        self.assertEqual(parsed.filters.vehicle_type, "bike")
        self.assertEqual(parsed.filters.min_range_km, 150)

    def test_parser_understands_price_range_between_values(self):
        parsed = parse_user_query("Best electric car for ₹15-20L?")
        self.assertEqual(parsed.filters.vehicle_type, "car")
        self.assertEqual(parsed.filters.min_price_inr, 1500000)
        self.assertEqual(parsed.filters.max_price_inr, 2000000)

    def test_greeting_does_not_return_random_vehicle_matches(self):
        result = self.rag.answer("hie")
        self.assertEqual(result.intent, "info")
        self.assertEqual(result.matches, [])
        self.assertIn("Hello!", result.answer)

    def test_extended_greeting_is_handled(self):
        result = self.rag.answer("good morning")
        self.assertEqual(result.intent, "info")
        self.assertEqual(result.matches, [])
        self.assertIn("Hello!", result.answer)

    def test_vague_recommendation_asks_for_clarification(self):
        result = self.rag.answer("best ev")
        self.assertEqual(result.intent, "recommendation")
        self.assertEqual(result.matches, [])
        self.assertIn("I can suggest the best EVs", result.answer)

    def test_comparison_locks_to_exact_requested_models(self):
        result = self.rag.answer("Compare Ola S1 Pro vs Ather 450X")
        names = [match.vehicle.name for match in result.matches]
        self.assertEqual(result.intent, "comparison")
        self.assertEqual(names, ["Ola S1 Pro", "Ather 450X"])

    def test_comparison_does_not_drift_to_sibling_variant(self):
        result = self.rag.answer("Compare Ather Rizta Z vs TVS iQube")
        names = [match.vehicle.name for match in result.matches]
        self.assertEqual(result.intent, "comparison")
        self.assertEqual(names, ["Ather Rizta Z", "TVS iQube"])

    def test_difference_between_models_is_treated_as_comparison(self):
        result = self.rag.answer("difference between Ola S1 Air and Ola S1 Pro")
        names = [match.vehicle.name for match in result.matches]
        self.assertEqual(result.intent, "comparison")
        self.assertEqual(names, ["Ola S1 Air", "Ola S1 Pro"])

    def test_comparison_asks_for_clarification_when_exact_model_not_in_dataset(self):
        result = self.rag.answer("Compare Ioniq 5 and EV6")
        self.assertEqual(result.intent, "comparison")
        self.assertEqual(result.matches, [])
        self.assertIn("I do not want to compare the wrong models", result.answer)
        self.assertIn("Hyundai Ioniq 5 N", result.answer)

    def test_car_recommendation_excludes_three_wheeler_entries(self):
        result = self.rag.answer("Best electric car for ₹15-20L?")
        names = [match.vehicle.name for match in result.matches]
        self.assertNotIn("Mahindra Electric ZEO", names)
        self.assertNotIn("Mahindra Electric Treo Zor", names)
        self.assertNotIn("Mahindra Electric E-Alfa Cargo", names)
        for match in result.matches:
            self.assertEqual(str(match.vehicle.metadata.get("category") or "").upper(), "4W")

    def test_three_wheeler_query_stays_inside_three_wheeler_category(self):
        result = self.rag.answer("Cheapest 3-wheeler EV?")
        self.assertEqual(result.intent, "recommendation")
        self.assertGreater(len(result.matches), 0)
        for match in result.matches:
            self.assertEqual(str(match.vehicle.metadata.get("category") or "").upper(), "3W")

    def test_budget_car_query_returns_multiple_sorted_cars(self):
        result = self.rag.answer("Show EV cars under 15 lakh")
        self.assertEqual(result.intent, "recommendation")
        self.assertGreaterEqual(len(result.matches), 3)
        prices = [match.vehicle.price_inr for match in result.matches[:3]]
        self.assertEqual(prices, sorted(prices))
        names = [match.vehicle.name for match in result.matches[:5]]
        self.assertNotIn("Tata Xpres T EV", names)
        self.assertNotIn("Tata Ace EV pro", names)
        self.assertNotIn("Tata Ace EV 1000", names)
        for match in result.matches[:5]:
            self.assertEqual(str(match.vehicle.metadata.get("category") or "").upper(), "4W")
            self.assertEqual((match.vehicle.vehicle_type or "").lower(), "car")

    def test_cheapest_three_wheeler_is_price_sorted(self):
        result = self.rag.answer("Cheapest 3-wheeler EV?")
        prices = [match.vehicle.price_inr for match in result.matches[:3]]
        self.assertEqual(prices, sorted(prices))

    def test_tco_is_answered_as_supported_knowledge(self):
        result = self.rag.answer("What is TCO?")
        self.assertEqual(result.intent, "info")
        self.assertEqual(result.matches, [])
        self.assertIn("Total Cost of Ownership", result.answer)

    def test_daily_commute_query_asks_targeted_follow_up(self):
        result = self.rag.answer("I travel 35 km daily, what should I buy?")
        self.assertEqual(result.intent, "recommendation")
        self.assertEqual(result.matches, [])
        self.assertIn("35 km daily commute", result.answer)
        self.assertIn("budget", result.answer)

    def test_limitations_question_is_answered_directly(self):
        result = self.rag.answer("What are your limitations as an advisor?")
        self.assertEqual(result.intent, "info")
        self.assertEqual(result.matches, [])
        self.assertIn("current EV dataset", result.answer)

    def test_rain_question_is_not_misread_as_comparison(self):
        result = self.rag.answer("can EVs work in rain?")
        self.assertEqual(result.intent, "info")
        self.assertEqual(result.matches, [])
        self.assertIn("safe", result.answer.lower())

    def test_location_query_uses_station_answer(self):
        result = self.rag.answer("charging stations near Bengaluru")
        self.assertEqual(result.intent, "info")
        self.assertEqual(result.matches, [])
        self.assertIn("charging locations", result.answer.lower())

    def test_bike_query_does_not_return_scooters(self):
        result = self.rag.answer("best bike for college student under 80000")
        for match in result.matches:
            self.assertNotEqual(match.vehicle.vehicle_type, "scooter")

    def test_subsidy_state_query_is_answered_directly(self):
        result = self.rag.answer("Maharashtra EV subsidy amount")
        self.assertEqual(result.intent, "info")
        self.assertEqual(result.matches, [])
        self.assertIn("Maharashtra", result.answer)


if __name__ == "__main__":
    unittest.main()
