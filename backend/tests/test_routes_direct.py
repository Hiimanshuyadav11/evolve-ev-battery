"""
Direct route function tests for EVolve without TestClient event-loop hang.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api.routes import profiles, charging, range as range_routes, trips, health, methods, data
from app.models.schemas import (
    VehicleProfileCreate,
    InterpolateRequest,
    EnergyCalculationRequest,
    ChargingTimeEstimateRequest,
    RangePredictRequest,
    TripFeasibilityRequest,
    BatteryHealthRequest,
    MethodComparisonRequest,
    ChargingReadingItem
)


class TestDirectRoutes(unittest.TestCase):

    def test_profiles_flow(self):
        # 1. List
        profs = profiles.list_profiles()
        self.assertGreaterEqual(len(profs), 1)

        # 2. Create
        new_prof = VehicleProfileCreate(
            name="Test Coupe",
            nominal_capacity_kwh=55.0,
            usable_capacity_kwh=50.0,
            original_usable_capacity_kwh=50.0,
            current_soc=60.0,
            notes="Direct test"
        )
        created = profiles.create_profile(new_prof)
        self.assertEqual(created["name"], "Test Coupe")
        p_id = created["id"]

        # 3. Get
        got = profiles.get_profile(p_id)
        self.assertEqual(got["usable_capacity_kwh"], 50.0)

        # 4. Clean up
        profiles.delete_profile(p_id)

    def test_charging_routes(self):
        req = InterpolateRequest(
            readings=[
                ChargingReadingItem(elapsed_minutes=0.0, soc_percent=20.0),
                ChargingReadingItem(elapsed_minutes=15.0, soc_percent=None),
                ChargingReadingItem(elapsed_minutes=30.0, soc_percent=40.0)
            ],
            method="linear"
        )
        inter_res = charging.interpolate_readings(req)
        self.assertEqual(inter_res["estimated_count"], 1)
        self.assertAlmostEqual(inter_res["readings"][1]["soc_percent"], 30.0, places=4)

        # Energy
        eng_req = EnergyCalculationRequest(
            t_minutes=[0.0, 30.0, 60.0],
            power_kw=[10.0, 10.0, 10.0],
            method="trapezoidal"
        )
        eng_res = charging.calculate_energy(eng_req)
        self.assertAlmostEqual(eng_res["total_energy_kwh"], 10.0, places=4)

    def test_range_route(self):
        req = RangePredictRequest(
            usable_capacity_kwh=60.0,
            current_soc_percent=50.0,
            consumption_kwh_per_km=0.2
        )
        res = range_routes.predict_range(req)
        self.assertAlmostEqual(res["range_prediction"]["expected_range_km"], 150.0, places=2)

    def test_trip_route(self):
        req = TripFeasibilityRequest(
            usable_capacity_kwh=60.0,
            starting_soc_percent=80.0,
            journey_distance_km=150.0,
            consumption_rate_kwh_per_km=0.2,
            desired_reserve_percent=10.0
        )
        res = trips.analyze_trip_feasibility(req)
        self.assertTrue(res["is_feasible"])
        self.assertAlmostEqual(res["arrival_soc_percent"], 30.0, places=1)

    def test_health_route(self):
        req = BatteryHealthRequest(
            original_usable_capacity_kwh=60.0,
            current_usable_capacity_kwh=54.0
        )
        res = health.estimate_soh(req)
        self.assertAlmostEqual(res["soh_percent"], 90.0, places=1)


if __name__ == "__main__":
    unittest.main()
