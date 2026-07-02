import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from services import subsidy_service
from services.subsidy_service import build_subsidy_snapshot, compute_central_subsidy, compute_tco_5year


class SubsidyServiceTests(unittest.TestCase):
    def setUp(self):
        self._original_cache = subsidy_service.LIVE_SUBSIDY_CACHE
        subsidy_service.LIVE_SUBSIDY_CACHE = {"maharashtra": 30000}

    def tearDown(self):
        subsidy_service.LIVE_SUBSIDY_CACHE = self._original_cache

    def test_two_wheeler_central_subsidy_is_capped(self):
        vehicle = SimpleNamespace(segment="TWO_WHEELER", battery_kwh=4.0)

        self.assertEqual(compute_central_subsidy(vehicle), 5000)

    def test_build_subsidy_snapshot_matches_existing_api_shape(self):
        vehicle = SimpleNamespace(
            id=7,
            segment="TWO_WHEELER",
            battery_kwh=2.0,
            fame2_subsidy_inr=0,
            state_subsidy_inr=10000,
            approx_price_inr=120000,
        )

        result = build_subsidy_snapshot(vehicle, state="Maharashtra", daily_km=30)

        self.assertTrue(result["success"])
        self.assertEqual(result["vehicle_id"], 7)
        self.assertEqual(result["state"], "maharashtra")
        self.assertEqual(result["central_subsidy_inr"], 5000)
        self.assertEqual(result["state_subsidy_inr"], 30000)
        self.assertEqual(result["total_applicable_subsidies"], 35000)
        self.assertEqual(result["tco_5year_inr"], compute_tco_5year(120000, 30, 35000))
        self.assertIn("policy_meta", result)

    def test_services_do_not_import_subsidy_route_module(self):
        services_dir = BACKEND_DIR / "services"
        offenders = []
        for file_path in services_dir.glob("*.py"):
            if "routes.subsidies" in file_path.read_text(encoding="utf-8", errors="replace"):
                offenders.append(file_path.name)

        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
