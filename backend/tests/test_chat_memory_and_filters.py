import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.ev_rag import EVRAGService
from services.ev_chat_retrieval import vehicle_supports_fast_charging
from core.config import settings


class ChatMemoryAndFiltersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._original_nvidia_enabled = settings.NVIDIA_RERANK_ENABLED
        cls._original_nvidia_key = settings.NVIDIA_API_KEY
        settings.NVIDIA_RERANK_ENABLED = False
        settings.NVIDIA_API_KEY = None
        cls.rag = EVRAGService()

    @classmethod
    def tearDownClass(cls):
        settings.NVIDIA_RERANK_ENABLED = cls._original_nvidia_enabled
        settings.NVIDIA_API_KEY = cls._original_nvidia_key

    def test_follow_up_inherits_budget_segment_and_state_filters(self):
        history = []

        first = self.rag.answer("I want a family EV. Budget 18 lakh.", history)
        history.extend([
            {"role": "user", "content": "I want a family EV. Budget 18 lakh."},
            {"role": "assistant", "content": first.answer},
        ])

        follow_up = self.rag.answer("Now make it in Karnataka and with fast charging only", history)
        self.assertEqual(follow_up.intent, "recommendation")
        self.assertEqual(follow_up.parsed_query.filters.vehicle_type, "car")
        self.assertEqual(follow_up.parsed_query.filters.max_price_inr, 1800000)
        self.assertEqual(follow_up.parsed_query.filters.state, "karnataka")
        self.assertTrue(follow_up.parsed_query.filters.fast_charging)
        self.assertGreaterEqual(len(follow_up.matches), 1)
        for match in follow_up.matches[:3]:
            self.assertLessEqual(match.vehicle.price_inr, 1800000)
            self.assertTrue(vehicle_supports_fast_charging(match.vehicle))

    def test_missing_segment_with_budget_and_home_charging_asks_clarification(self):
        result = self.rag.answer("I need an EV in Delhi under 15 lakh with home charging")
        self.assertEqual(result.intent, "recommendation")
        self.assertEqual(result.matches, [])
        self.assertIn("segment", result.answer.lower())
        self.assertIn("scooter", result.answer.lower())
        self.assertIn("car", result.answer.lower())

    def test_out_of_domain_query_falls_back_cleanly(self):
        result = self.rag.answer("Who won yesterday's cricket match?")
        self.assertEqual(result.intent, "info")
        self.assertEqual(result.matches, [])
        self.assertEqual("Not enough data available", result.answer)

    def test_explicit_fast_charging_filter_returns_fast_charging_matches(self):
        result = self.rag.answer("Best EV cars under 20 lakh with fast charging only")
        self.assertEqual(result.intent, "recommendation")
        self.assertGreaterEqual(len(result.matches), 1)
        for match in result.matches[:5]:
            self.assertTrue(vehicle_supports_fast_charging(match.vehicle))


if __name__ == "__main__":
    unittest.main()
