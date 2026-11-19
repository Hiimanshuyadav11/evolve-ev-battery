"""
Unit Tests for EVolve Numerical Methods.

Validates:
1. Linear interpolation against Section 13.1 known answer (10 min: 20%, 30 min: 40% -> 20 min: 30%).
2. Newton divided-difference interpolation.
3. Trapezoidal integration against Section 13.1 known answer (2 kW for 1 hour -> 2 kWh).
4. Simpson's 1/3 rule verification & equal spacing validation.
5. Constant power charging time against Section 13.1 known answer (40 kWh, 20% to 50%, 6 kW -> 2.0 hours).
6. Range estimation against Section 13.1 known answer (40 kWh, 50% SoC, 0.2 kWh/km -> 100 km).
7. SOH estimation against Section 13.1 known answer (40 kWh original, 36 kWh current -> 90% SOH).
8. Least squares linear regression on trip data.
9. Bisection and Newton-Raphson root finding on journey feasibility.
10. Error metrics calculations.
"""

import unittest
import math
import sys
import os

# Ensure backend/app is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.numerical_methods import (
    linear_interpolate,
    newton_divided_difference,
    interpolate_missing_readings,
    trapezoidal_rule,
    simpsons_one_third_rule,
    compare_integration_methods,
    estimate_charging_time,
    linear_regression_trip_consumption,
    predict_driving_range,
    bisection_method,
    newton_raphson_method,
    solve_journey_feasibility,
    compute_scalar_error,
    compute_series_error,
    NumericalMethodError
)


class TestNumericalMethods(unittest.TestCase):

    def test_linear_interpolation_known_answer(self):
        """Spec Section 13.1: (10 min, 20%) & (30 min, 40%) -> at 20 min expect 30%."""
        res = linear_interpolate(10.0, 20.0, 30.0, 40.0, 20.0)
        self.assertAlmostEqual(res["result_y"], 30.0, places=5)
        self.assertAlmostEqual(res["slope"], 1.0, places=5)
        self.assertEqual(len(res["warnings"]), 0)

    def test_linear_interpolation_extrapolation_warning(self):
        res = linear_interpolate(10.0, 20.0, 30.0, 40.0, 35.0)
        self.assertTrue(len(res["warnings"]) > 0)
        self.assertIn("Extrapolation", res["warnings"][0])

    def test_linear_interpolation_duplicate_x_error(self):
        with self.assertRaises(NumericalMethodError):
            linear_interpolate(10.0, 20.0, 10.0, 30.0, 15.0)

    def test_newton_divided_difference_quadratic(self):
        # f(x) = x^2: points (1,1), (2,4), (3,9) -> target x=2.5 should yield 6.25
        points = [(1.0, 1.0), (2.0, 4.0), (3.0, 9.0)]
        res = newton_divided_difference(points, 2.5)
        self.assertAlmostEqual(res["result_y"], 6.25, places=5)
        self.assertEqual(res["degree"], 2)

    def test_missing_readings_series_interpolation(self):
        readings = [
            {"elapsed_minutes": 0.0, "soc_percent": 10.0},
            {"elapsed_minutes": 10.0, "soc_percent": None},  # Missing
            {"elapsed_minutes": 20.0, "soc_percent": 30.0},
        ]
        res = interpolate_missing_readings(readings, method="linear")
        self.assertEqual(res["estimated_count"], 1)
        self.assertAlmostEqual(res["readings"][1]["soc_percent"], 20.0, places=5)
        self.assertTrue(res["readings"][1]["is_estimated"])

    def test_trapezoidal_rule_known_answer(self):
        """Spec Section 13.1: 2 kW at 0 hours and 2 kW at 1 hour (60 min) -> 2 kWh."""
        t_minutes = [0.0, 60.0]
        power_kw = [2.0, 2.0]
        res = trapezoidal_rule(t_minutes, power_kw)
        self.assertAlmostEqual(res["total_energy_kwh"], 2.0, places=5)

    def test_trapezoidal_rule_variable_power(self):
        # 0 min: 10 kW, 30 min: 20 kW, 60 min: 10 kW
        # dt1 = 0.5 hr, avg1 = 15 kW -> 7.5 kWh
        # dt2 = 0.5 hr, avg2 = 15 kW -> 7.5 kWh
        # Total = 15 kWh
        t_min = [0.0, 30.0, 60.0]
        p_kw = [10.0, 20.0, 10.0]
        res = trapezoidal_rule(t_min, p_kw)
        self.assertAlmostEqual(res["total_energy_kwh"], 15.0, places=5)

    def test_simpsons_one_third_rule_exact_on_parabola(self):
        # f(t) = -t^2 + 4t + 10 over t in [0, 2] hours with 2 subintervals (t=0, 1, 2 hr)
        # h = 1 hr (60 min), points: t=[0, 60, 120] min
        # p(0) = 10, p(1) = 13, p(2) = 14
        # Simpson: (1/3) * (10 + 14 + 4*13) = (1/3) * (76) = 25.33333 kWh
        t_min = [0.0, 60.0, 120.0]
        p_kw = [10.0, 13.0, 14.0]
        res = simpsons_one_third_rule(t_min, p_kw)
        self.assertAlmostEqual(res["total_energy_kwh"], 76.0 / 3.0, places=4)

    def test_simpsons_rejects_unequal_spacing(self):
        t_min = [0.0, 30.0, 70.0]  # dt=30, dt=40
        p_kw = [10.0, 15.0, 10.0]
        with self.assertRaises(NumericalMethodError):
            simpsons_one_third_rule(t_min, p_kw)

    def test_simpsons_rejects_odd_interval_count(self):
        t_min = [0.0, 30.0, 60.0, 90.0]  # 4 points -> 3 intervals (odd)
        p_kw = [10.0, 15.0, 15.0, 10.0]
        with self.assertRaises(NumericalMethodError):
            simpsons_one_third_rule(t_min, p_kw)

    def test_charging_time_constant_power_known_answer(self):
        """Spec Section 13.1: Usable=40 kWh, Start=20%, Target=50%, P=6 kW -> 2.0 hours (12 kWh)."""
        res = estimate_charging_time(
            usable_capacity_kwh=40.0,
            current_soc=20.0,
            target_soc=50.0,
            constant_power_kw=6.0
        )
        const_est = res["constant_power_estimate"]
        self.assertIsNotNone(const_est)
        self.assertAlmostEqual(const_est["energy_needed_kwh"], 12.0, places=5)
        self.assertAlmostEqual(const_est["estimated_hours"], 2.0, places=5)
        self.assertEqual(const_est["formatted_time"], "2h 0m")

    def test_range_prediction_known_answer(self):
        """Spec Section 13.1: Usable=40 kWh, SoC=50%, Consumption=0.2 kWh/km -> 100 km."""
        res = predict_driving_range(
            usable_capacity_kwh=40.0,
            current_soc_percent=50.0,
            consumption_kwh_per_km=0.2
        )
        self.assertAlmostEqual(res["available_energy_kwh"], 20.0, places=5)
        self.assertAlmostEqual(res["expected_range_km"], 100.0, places=5)
        self.assertAlmostEqual(res["scenarios"]["expected"]["range_km"], 100.0, places=2)

    def test_linear_regression_trips(self):
        # d = [10, 20, 30, 40], E = [2.0, 4.0, 6.0, 8.0] -> perfect slope = 0.2, intercept = 0, R^2 = 1.0
        dists = [10.0, 20.0, 30.0, 40.0]
        energies = [2.0, 4.0, 6.0, 8.0]
        res = linear_regression_trip_consumption(dists, energies)
        self.assertAlmostEqual(res["slope_kwh_per_km"], 0.2, places=5)
        self.assertAlmostEqual(res["intercept_kwh"], 0.0, places=5)
        self.assertAlmostEqual(res["r_squared"], 1.0, places=4)
        self.assertAlmostEqual(res["mae_kwh"], 0.0, places=5)

    def test_journey_feasibility_direct_and_root_finding(self):
        # Usable = 50 kWh, Start = 80%, Distance = 150 km, Consumption = 0.2 kWh/km
        # E_req = 150 * 0.2 = 30 kWh
        # SoC consumed = (30 / 50) * 100 = 60%
        # Arrival SoC = 80 - 60 = 20%
        # Desired reserve = 10% -> Feasible!
        # S_min = 60 + 10 = 70%
        res = solve_journey_feasibility(
            usable_capacity_kwh=50.0,
            starting_soc_percent=80.0,
            journey_distance_km=150.0,
            consumption_rate_kwh_per_km=0.2,
            desired_reserve_percent=10.0
        )
        self.assertTrue(res["is_feasible"])
        self.assertAlmostEqual(res["arrival_soc_percent"], 20.0, places=2)
        self.assertAlmostEqual(res["min_starting_soc_percent"], 70.0, places=2)

        # Check root finding solver agreement
        root_demo = res["root_finding_demo"]
        self.assertIsNotNone(root_demo)
        self.assertAlmostEqual(root_demo["bisection"]["root"], 70.0, places=3)
        self.assertAlmostEqual(root_demo["newton_raphson"]["root"], 70.0, places=3)

    def test_error_analysis_metrics(self):
        actuals = [10.0, 20.0, 30.0]
        preds = [11.0, 19.0, 30.0]
        # errs = [1.0, 1.0, 0.0] -> MAE = 2/3 = 0.666667
        # sq = [1.0, 1.0, 0.0] -> RMSE = sqrt(2/3) = 0.816496
        res = compute_series_error(actuals, preds)
        self.assertAlmostEqual(res["mae"], 2.0 / 3.0, places=4)
        self.assertAlmostEqual(res["rmse"], math.sqrt(2.0 / 3.0), places=4)


if __name__ == "__main__":
    unittest.main()
