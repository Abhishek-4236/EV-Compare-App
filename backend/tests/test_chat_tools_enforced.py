import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from services.ev_rag import EVRAGService, NO_VERIFIED_DATA_MESSAGE
from services.ev_rag_types import RetrievalMatch, VehicleDocument
from services.ev_tools import ToolResult


class ToolEnforcementTests(unittest.TestCase):
    def setUp(self):
        self.rag = EVRAGService()

    def _fake_doc(self, name: str, brand: str, model: str) -> VehicleDocument:
        return VehicleDocument(
            id="doc-1",
            content=None,
            name=name,
            brand=brand,
            model=model,
            vehicle_type="scooter",
            price_inr=120000,
            range_km=120,
            battery_kwh=3.0,
            charging_time=None,
            charging_type="AC",
            features=[],
            source_row=1,
            metadata={"category": "2W"},
        )

    def test_on_road_price_without_state_asks_for_state(self):
        doc = self._fake_doc("Ola S1 Pro", "Ola", "S1 Pro")
        fake_db = MagicMock()

        row = MagicMock()
        row.id = 101
        row.brand = "Ola"
        row.model = "S1 Pro"
        row.segment = "TWO_WHEELER"
        row.category = "2W"
        row.vehicle_type = "scooter"
        row.approx_price_inr = 120000
        row.range_km = 120
        row.battery_kwh = 3.0
        row.top_speed_kmh = 90
        row.charging_type = "AC"
        row.overall_rating = 4.2
        row.fame2_subsidy_inr = 0
        row.state_subsidy_inr = 0

        fake_db.query.return_value.filter.return_value.first.return_value = row

        with patch("services.ev_rag.resolve_named_vehicles", return_value=[doc]):
            result = self.rag.answer("What is the on-road price of Ola S1 Pro?", [], db=fake_db)

        self.assertIn("Which state", result.answer)

    def test_missing_model_returns_exact_no_verified_data(self):
        doc = self._fake_doc("Imaginary EV X", "Imaginary", "EV X")
        fake_db = MagicMock()
        fake_db.query.return_value.filter.return_value.first.return_value = None

        with patch("services.ev_rag.resolve_named_vehicles", return_value=[doc]):
            result = self.rag.answer("price of Imaginary EV X", [], db=fake_db)

        self.assertEqual(result.answer, NO_VERIFIED_DATA_MESSAGE)

    def test_comparison_uses_tool_output_table(self):
        left = self._fake_doc("Ola S1 Pro", "Ola", "S1 Pro")
        right = self._fake_doc("Ather 450X", "Ather", "450X")

        fake_db = MagicMock()

        row_left = MagicMock()
        row_left.id = 201
        row_left.brand = "Ola"
        row_left.model = "S1 Pro"
        row_left.segment = "TWO_WHEELER"
        row_left.category = "2W"
        row_left.vehicle_type = "scooter"
        row_left.approx_price_inr = 120000
        row_left.range_km = 120
        row_left.battery_kwh = 3.0
        row_left.top_speed_kmh = 90
        row_left.charging_type = "AC"
        row_left.overall_rating = 4.2
        row_left.fame2_subsidy_inr = 0
        row_left.state_subsidy_inr = 0

        row_right = MagicMock()
        row_right.id = 202
        row_right.brand = "Ather"
        row_right.model = "450X"
        row_right.segment = "TWO_WHEELER"
        row_right.category = "2W"
        row_right.vehicle_type = "scooter"
        row_right.approx_price_inr = 135000
        row_right.range_km = 110
        row_right.battery_kwh = 2.9
        row_right.top_speed_kmh = 85
        row_right.charging_type = "AC"
        row_right.overall_rating = 4.1
        row_right.fame2_subsidy_inr = 0
        row_right.state_subsidy_inr = 0

        def first_side_effect():
            # Called multiple times; return left then right then left/right by id lookup.
            yield row_left
            yield row_right
            while True:
                yield row_left

        first_iter = first_side_effect()
        fake_db.query.return_value.filter.return_value.first.side_effect = lambda: next(first_iter)

        fake_tool = ToolResult(
            tool="compare_vehicles",
            ok=True,
            data={
                "success": True,
                "vehicles": [
                    {
                        "id": 201,
                        "name": "Ola S1 Pro",
                        "approx_price_inr": 120000,
                        "range_km": 120,
                        "battery_kwh": 3.0,
                        "top_speed_kmh": 90,
                        "charging_type": "AC",
                        "overall_rating": 4.2,
                        "fame2_subsidy_inr": 0,
                        "cost_efficiency": 100.0,
                        "value_score": 12.3,
                    },
                    {
                        "id": 202,
                        "name": "Ather 450X",
                        "approx_price_inr": 135000,
                        "range_km": 110,
                        "battery_kwh": 2.9,
                        "top_speed_kmh": 85,
                        "charging_type": "AC",
                        "overall_rating": 4.1,
                        "fame2_subsidy_inr": 0,
                        "cost_efficiency": 81.5,
                        "value_score": 11.8,
                    },
                ],
            },
        )

        matches = [
            RetrievalMatch(vehicle=left, score=1.0, matched_on=["name_exact"]),
            RetrievalMatch(vehicle=right, score=1.0, matched_on=["name_exact"]),
        ]

        with patch.object(self.rag, "_comparison_matches", return_value=(matches, None)):
            with patch("services.ev_rag.tool_compare_vehicles", return_value=fake_tool):
                result = self.rag.answer("Compare Ola S1 Pro vs Ather 450X", [], db=fake_db)

        self.assertIn("| Feature |", result.answer)
        self.assertIn("Value score", result.answer)


if __name__ == "__main__":
    unittest.main()

