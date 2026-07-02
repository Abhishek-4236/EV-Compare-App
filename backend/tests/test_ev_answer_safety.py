import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from services.ev_answer_safety import STRICT_NO_DATA_MESSAGE, confidence_level, validate_grounding
from services.ev_rag_types import ParsedQuery, QueryFilters, RetrievalMatch, VehicleDocument


def _vehicle(name: str = "Tata Tiago EV") -> VehicleDocument:
    return VehicleDocument(
        id="1",
        content=None,
        name=name,
        brand=name.split()[0],
        model=" ".join(name.split()[1:]),
        vehicle_type="car",
        price_inr=800000,
        range_km=250,
        battery_kwh=19.2,
        charging_time=None,
        charging_type="AC",
        features=[],
        source_row=1,
        metadata={"category": "4W"},
    )


class EVAnswerSafetyTests(unittest.TestCase):
    def test_validate_grounding_rejects_no_context(self):
        self.assertEqual(
            validate_grounding("Any answer", "Fallback", [], []),
            STRICT_NO_DATA_MESSAGE,
        )

    def test_validate_grounding_falls_back_on_unsupported_vehicle(self):
        fallback = "Tata Tiago EV costs ₹8.00 lakh."
        match = RetrievalMatch(vehicle=_vehicle(), score=1.0, matched_on=["test"])

        answer = validate_grounding(
            "Tata Tiago EV is good, and MG ZS EV is also under budget.",
            fallback,
            ["Tata Tiago EV price 800000 range 250"],
            [match],
        )

        self.assertEqual(answer, fallback)

    def test_recommendation_confidence_uses_query_anchors(self):
        parsed = ParsedQuery(
            intent="recommendation",
            rewritten_query="best car under 15 lakh",
            filters=QueryFilters(vehicle_type="car", max_price_inr=1500000),
        )
        match = RetrievalMatch(vehicle=_vehicle(), score=1.0, matched_on=["test"])

        self.assertEqual(confidence_level(parsed, [match]), "medium")


if __name__ == "__main__":
    unittest.main()
