"""
Numerical Methods - Linear Regression & Range Prediction Module for EVolve.

Implements:
1. Least Squares Linear Regression (Distance vs Energy Consumed).
2. Goodness-of-fit metrics: R-squared, MAE, RMSE, and Residuals.
3. Simple mean consumption baseline comparison.
4. Range prediction with conservative, expected, and optimistic scenarios.
"""

from typing import List, Tuple, Dict, Any, Optional
import math
from .interpolation import NumericalMethodError


def linear_regression_trip_consumption(
    distance_km: List[float], energy_consumed_kwh: List[float]
) -> Dict[str, Any]:
    """
    Fits least squares linear regression model: Energy = a + b * Distance
    Where slope b represents marginal consumption (kWh/km)
    and intercept a represents baseline/idle overhead energy (kWh).
    
    Also computes:
    - Baseline average consumption c_mean = sum(Energy) / sum(Distance)
    - Coefficient of determination R^2
    - Mean Absolute Error (MAE)
    - Root Mean Squared Error (RMSE)
    - Residuals for each point: e_i = y_i - (a + b * x_i)
    """
    n = len(distance_km)
    if n < 2 or len(energy_consumed_kwh) != n:
        raise NumericalMethodError("At least 2 trip records are required for linear regression analysis.")

    # Validate inputs are positive
    for i in range(n):
        if distance_km[i] <= 0:
            raise NumericalMethodError(f"Trip distance must be positive. Found {distance_km[i]} km at index {i}.")
        if energy_consumed_kwh[i] < 0:
            raise NumericalMethodError(f"Consumed energy cannot be negative. Found {energy_consumed_kwh[i]} kWh at index {i}.")

    sum_x = sum(distance_km)
    sum_y = sum(energy_consumed_kwh)
    mean_x = sum_x / n
    mean_y = sum_y / n

    # Compute variance terms
    ss_xx = sum((x - mean_x) ** 2 for x in distance_km)
    ss_xy = sum((distance_km[i] - mean_x) * (energy_consumed_kwh[i] - mean_y) for i in range(n))
    ss_yy = sum((y - mean_y) ** 2 for y in energy_consumed_kwh)

    if math.isclose(ss_xx, 0.0, abs_tol=1e-9):
        raise NumericalMethodError(
            "All trip distances are identical. Slope cannot be determined (division by zero in SS_xx)."
        )

    # Slope b and Intercept a
    b_slope = ss_xy / ss_xx  # kWh per km
    a_intercept = mean_y - b_slope * mean_x  # kWh

    # Baseline average consumption (direct ratio)
    c_mean_kwh_per_km = sum_y / sum_x
    c_mean_kwh_per_100km = c_mean_kwh_per_km * 100.0

    # Predictions and residuals
    residuals = []
    abs_errors = []
    sq_errors = []
    point_evaluations = []

    for i in range(n):
        x = distance_km[i]
        y_actual = energy_consumed_kwh[i]
        y_pred = a_intercept + b_slope * x
        residual = y_actual - y_pred
        abs_err = abs(residual)
        sq_err = residual ** 2

        residuals.append(residual)
        abs_errors.append(abs_err)
        sq_errors.append(sq_err)

        point_evaluations.append({
            "index": i + 1,
            "distance_km": x,
            "actual_kwh": y_actual,
            "predicted_kwh": round(y_pred, 4),
            "residual": round(residual, 4),
            "abs_error": round(abs_err, 4),
            "actual_rate_kwh_per_km": round(y_actual / x, 4)
        })

    # Error metrics
    ss_res = sum(sq_errors)
    r_squared = (1.0 - (ss_res / ss_yy)) if ss_yy > 1e-9 else 1.0
    # Clamping R^2 between 0 and 1
    r_squared = max(0.0, min(1.0, r_squared))
    
    mae = sum(abs_errors) / n
    rmse = math.sqrt(ss_res / n)

    warnings = []
    if n < 5:
        warnings.append(f"Small sample size ({n} trips). Statistical significance of regression is limited.")
    if r_squared < 0.6:
        warnings.append(f"Low R-squared ({r_squared:.2f}). Trip energy exhibits high variance from simple linear model.")

    steps = [
        f"1. Calculated sums for {n} observations: sum(d) = {sum_x:.2f} km, sum(E) = {sum_y:.2f} kWh",
        f"2. Means: x_bar = {mean_x:.2f} km, y_bar = {mean_y:.2f} kWh",
        f"3. Sum of squares: SS_xx = {ss_xx:.4f}, SS_xy = {ss_xy:.4f}, SS_yy = {ss_yy:.4f}",
        f"4. Slope b = SS_xy / SS_xx = {ss_xy:.4f} / {ss_xx:.4f} = {b_slope:.6f} kWh/km ({b_slope*100:.2f} kWh/100km)",
        f"5. Intercept a = y_bar - b * x_bar = {mean_y:.4f} - ({b_slope:.6f} * {mean_x:.4f}) = {a_intercept:.6f} kWh",
        f"6. Fitted equation: Energy(d) = {a_intercept:.4f} + {b_slope:.4f} * d",
        f"7. Baseline direct average: {c_mean_kwh_per_km:.4f} kWh/km ({c_mean_kwh_per_100km:.2f} kWh/100km)",
        f"8. Goodness-of-fit: R^2 = {r_squared:.4f}, MAE = {mae:.4f} kWh, RMSE = {rmse:.4f} kWh"
    ]

    return {
        "method": "Least Squares Linear Regression",
        "sample_size": n,
        "slope_kwh_per_km": round(b_slope, 6),
        "slope_kwh_per_100km": round(b_slope * 100.0, 4),
        "intercept_kwh": round(a_intercept, 6),
        "equation": f"Energy = {a_intercept:.4f} + {b_slope:.4f} * Distance",
        "baseline_mean_rate_kwh_per_km": round(c_mean_kwh_per_km, 6),
        "baseline_mean_rate_kwh_per_100km": round(c_mean_kwh_per_100km, 4),
        "r_squared": round(r_squared, 4),
        "mae_kwh": round(mae, 4),
        "rmse_kwh": round(rmse, 4),
        "points": point_evaluations,
        "steps": steps,
        "warnings": warnings
    }


def predict_driving_range(
    usable_capacity_kwh: float,
    current_soc_percent: float,
    consumption_kwh_per_km: float
) -> Dict[str, Any]:
    """
    Predicts approximate driving range based on usable battery energy and consumption rate.
    
    Formulas:
    E_available = usable_capacity_kwh * (current_soc_percent / 100.0)
    Range = E_available / consumption_kwh_per_km
    
    Provides 3 operational scenarios:
    - Conservative: 15% higher consumption (heavy traffic / cold weather / highway speed)
    - Expected: nominal entered/fitted consumption
    - Optimistic: 15% lower consumption (mild weather / city eco-driving)
    """
    if usable_capacity_kwh <= 0:
        raise NumericalMethodError("Usable capacity must be strictly positive.")
    if not (0.0 <= current_soc_percent <= 100.0):
        raise NumericalMethodError("Current SoC must be between 0% and 100%.")
    if consumption_kwh_per_km <= 0:
        raise NumericalMethodError("Consumption rate must be strictly positive (greater than 0 kWh/km).")

    available_energy_kwh = usable_capacity_kwh * (current_soc_percent / 100.0)
    expected_range_km = available_energy_kwh / consumption_kwh_per_km

    # Conservative scenario (+15% consumption -> lower range)
    cons_rate = consumption_kwh_per_km * 1.15
    conservative_range_km = available_energy_kwh / cons_rate

    # Optimistic scenario (-15% consumption -> higher range)
    opt_rate = consumption_kwh_per_km * 0.85
    optimistic_range_km = available_energy_kwh / opt_rate

    steps = [
        f"1. Usable Capacity = {usable_capacity_kwh} kWh, Current SoC = {current_soc_percent}%",
        f"2. Available Energy E_avail = {usable_capacity_kwh} * ({current_soc_percent} / 100) = {available_energy_kwh:.4f} kWh",
        f"3. Expected Consumption = {consumption_kwh_per_km:.4f} kWh/km ({consumption_kwh_per_km * 100:.2f} kWh/100km)",
        f"4. Expected Range R = E_avail / c = {available_energy_kwh:.4f} / {consumption_kwh_per_km:.4f} = {expected_range_km:.2f} km",
        f"5. Conservative Scenario (+15% consumption = {cons_rate:.4f} kWh/km): {conservative_range_km:.2f} km",
        f"6. Optimistic Scenario (-15% consumption = {opt_rate:.4f} kWh/km): {optimistic_range_km:.2f} km"
    ]

    return {
        "usable_capacity_kwh": usable_capacity_kwh,
        "current_soc_percent": current_soc_percent,
        "available_energy_kwh": round(available_energy_kwh, 4),
        "consumption_kwh_per_km": round(consumption_kwh_per_km, 6),
        "consumption_kwh_per_100km": round(consumption_kwh_per_km * 100.0, 4),
        "expected_range_km": round(expected_range_km, 2),
        "scenarios": {
            "conservative": {
                "label": "Conservative (+15% consumption: highway/cold)",
                "consumption_rate": round(cons_rate, 4),
                "range_km": round(conservative_range_km, 2)
            },
            "expected": {
                "label": "Expected (Nominal observation)",
                "consumption_rate": round(consumption_kwh_per_km, 4),
                "range_km": round(expected_range_km, 2)
            },
            "optimistic": {
                "label": "Optimistic (-15% consumption: mild/city)",
                "consumption_rate": round(opt_rate, 4),
                "range_km": round(optimistic_range_km, 2)
            }
        },
        "steps": steps,
        "assumptions": (
            "Linear mapping of SoC to energy; constant consumption rate across trip; "
            "auxiliary loads (HVAC) assumed included in the observation."
        )
    }
