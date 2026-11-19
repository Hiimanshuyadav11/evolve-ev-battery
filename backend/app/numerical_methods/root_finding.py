"""
Numerical Methods - Root Finding Module for EVolve.

Implements:
1. Bisection Method with iterative bracket tracking.
2. Newton-Raphson Method with derivative tracking and safeguards.
3. Journey Feasibility Root-Finding Model:
   Find starting SoC S such that f(S) = E_avail(S) - E_journey - E_reserve = 0
   with optional nonlinear aerodynamic drag consumption function c(v).
"""

from typing import List, Tuple, Dict, Any, Callable, Optional
import math
from .interpolation import NumericalMethodError


def bisection_method(
    f: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-5,
    max_iter: int = 50
) -> Dict[str, Any]:
    """
    Finds root of continuous function f in interval [a, b] using Bisection Method.
    Requires f(a) * f(b) <= 0.
    """
    fa = f(a)
    fb = f(b)

    if fa * fb > 0:
        raise NumericalMethodError(
            f"Bisection bracket condition violated: f(a) and f(b) must have opposite signs. "
            f"f({a}) = {fa:.6f}, f({b}) = {fb:.6f}"
        )

    iterations = []
    curr_a = a
    curr_b = b

    for k in range(1, max_iter + 1):
        m = (curr_a + curr_b) / 2.0
        fm = f(m)
        interval_width = abs(curr_b - curr_a)

        iterations.append({
            "iteration": k,
            "a": round(curr_a, 6),
            "b": round(curr_b, 6),
            "midpoint_m": round(m, 6),
            "f_m": round(fm, 6),
            "interval_width": round(interval_width, 6)
        })

        if abs(fm) < tol or interval_width < tol:
            return {
                "method": "Bisection Method",
                "root": round(m, 6),
                "f_root": round(fm, 8),
                "iterations_count": k,
                "converged": True,
                "tolerance": tol,
                "history": iterations,
                "formula": "m = (a + b) / 2; interval halved each step until |b - a| < tol"
            }

        # Update bracket
        if fa * fm < 0:
            curr_b = m
            fb = fm
        else:
            curr_a = m
            fa = fm

    return {
        "method": "Bisection Method",
        "root": round((curr_a + curr_b) / 2.0, 6),
        "f_root": round(f((curr_a + curr_b) / 2.0), 8),
        "iterations_count": max_iter,
        "converged": False,
        "warning": f"Maximum iterations ({max_iter}) reached without meeting tolerance.",
        "tolerance": tol,
        "history": iterations
    }


def newton_raphson_method(
    f: Callable[[float], float],
    df: Callable[[float], float],
    x0: float,
    tol: float = 1e-6,
    max_iter: int = 50
) -> Dict[str, Any]:
    """
    Finds root using Newton-Raphson Method:
    x_{n+1} = x_n - f(x_n) / f'(x_n)
    
    Includes safeguards for zero or near-zero derivatives.
    """
    x = x0
    iterations = []

    for k in range(1, max_iter + 1):
        fx = f(x)
        dfx = df(x)

        if abs(dfx) < 1e-12:
            raise NumericalMethodError(
                f"Near-zero derivative encountered at x = {x:.6f} (f'(x) = {dfx}). "
                f"Newton-Raphson division by zero prevention triggered."
            )

        dx = fx / dfx
        x_next = x - dx

        iterations.append({
            "iteration": k,
            "x_k": round(x, 6),
            "f_x": round(fx, 6),
            "df_x": round(dfx, 6),
            "delta_x": round(dx, 6),
            "x_next": round(x_next, 6)
        })

        if abs(fx) < tol or abs(dx) < tol:
            return {
                "method": "Newton-Raphson Method",
                "root": round(x_next, 6),
                "f_root": round(f(x_next), 8),
                "iterations_count": k,
                "converged": True,
                "tolerance": tol,
                "history": iterations,
                "formula": "x_{k+1} = x_k - (f(x_k) / f'(x_k))"
            }

        x = x_next

    return {
        "method": "Newton-Raphson Method",
        "root": round(x, 6),
        "f_root": round(f(x), 8),
        "iterations_count": max_iter,
        "converged": False,
        "warning": f"Maximum iterations ({max_iter}) reached without meeting tolerance.",
        "tolerance": tol,
        "history": iterations
    }


def solve_journey_feasibility(
    usable_capacity_kwh: float,
    starting_soc_percent: float,
    journey_distance_km: float,
    consumption_rate_kwh_per_km: float,
    desired_reserve_percent: float = 10.0,
    use_root_finding_demo: bool = True
) -> Dict[str, Any]:
    """
    Evaluates journey feasibility:
    Inputs:
    - Usable battery capacity (kWh)
    - Starting SoC (%)
    - Journey distance (km)
    - Consumption rate (kWh/km)
    - Desired arrival reserve SoC (%)
    
    Calculations:
    - Energy required: E_req = distance * consumption
    - Percentage consumed: delta_SoC = (E_req / usable_capacity) * 100
    - Estimated arrival SoC: S_arrival = starting_soc - delta_SoC
    - Minimum starting SoC needed: S_min = delta_SoC + desired_reserve
    - Feasibility status & explainable diagnosis
    """
    if usable_capacity_kwh <= 0:
        raise NumericalMethodError("Usable battery capacity must be positive.")
    if not (0.0 <= starting_soc_percent <= 100.0):
        raise NumericalMethodError("Starting SoC must be between 0% and 100%.")
    if journey_distance_km <= 0:
        raise NumericalMethodError("Journey distance must be positive.")
    if consumption_rate_kwh_per_km <= 0:
        raise NumericalMethodError("Consumption rate must be positive.")
    if not (0.0 <= desired_reserve_percent <= 50.0):
        raise NumericalMethodError("Desired reserve percentage must be between 0% and 50%.")

    energy_required_kwh = journey_distance_km * consumption_rate_kwh_per_km
    soc_consumed_percent = (energy_required_kwh / usable_capacity_kwh) * 100.0
    arrival_soc_percent = starting_soc_percent - soc_consumed_percent
    min_starting_soc_percent = soc_consumed_percent + desired_reserve_percent

    # Feasibility evaluation
    is_feasible = arrival_soc_percent >= desired_reserve_percent
    will_reach_zero = arrival_soc_percent < 0.0

    if will_reach_zero:
        status = "INFEASIBLE_DEPLETION"
        message = (
            f"Journey will exhaust battery completely before destination! "
            f"Estimated arrival charge is {arrival_soc_percent:.1f}%. "
            f"You need at least {min_starting_soc_percent:.1f}% charge (or an en-route charging stop)."
        )
    elif not is_feasible:
        status = "RESERVE_BREACHED"
        message = (
            f"Vehicle can physically reach destination with {arrival_soc_percent:.1f}% charge, "
            f"but this breaches your target reserve of {desired_reserve_percent:.1f}%."
        )
    else:
        status = "FEASIBLE"
        message = (
            f"Journey is feasible with comfortable margin. Expected arrival charge is {arrival_soc_percent:.1f}% "
            f"(reserving >= {desired_reserve_percent:.1f}%)."
        )

    # Academic Demonstration: Root-finding demonstration for S_min
    # f(S) = (Cu * S / 100) - E_req - (Cu * S_reserve / 100) = 0
    root_demo = None
    if use_root_finding_demo:
        def residual_f(s: float) -> float:
            return (usable_capacity_kwh * (s / 100.0)) - energy_required_kwh - (usable_capacity_kwh * (desired_reserve_percent / 100.0))

        def d_residual_f(s: float) -> float:
            return usable_capacity_kwh / 100.0

        # Run bisection on [0, 150]
        # Check signs
        if residual_f(0.0) * residual_f(150.0) <= 0:
            bisect_res = bisection_method(residual_f, 0.0, 150.0, tol=1e-4)
            newton_res = newton_raphson_method(residual_f, d_residual_f, x0=50.0, tol=1e-4)
            root_demo = {
                "bisection": bisect_res,
                "newton_raphson": newton_res,
                "direct_formula_s_min": round(min_starting_soc_percent, 4),
                "academic_explanation": (
                    "In the Methods Lab, this illustrates numerical root-finding where the exact solution "
                    "S_min = 100 * (E_req / Cu) + S_reserve is verified against iterative Bisection and Newton-Raphson solvers."
                )
            }

    return {
        "usable_capacity_kwh": usable_capacity_kwh,
        "starting_soc_percent": starting_soc_percent,
        "journey_distance_km": journey_distance_km,
        "consumption_rate_kwh_per_km": round(consumption_rate_kwh_per_km, 6),
        "desired_reserve_percent": desired_reserve_percent,
        "energy_required_kwh": round(energy_required_kwh, 4),
        "soc_consumed_percent": round(soc_consumed_percent, 2),
        "arrival_soc_percent": round(arrival_soc_percent, 2),
        "min_starting_soc_percent": round(min_starting_soc_percent, 2),
        "is_feasible": is_feasible,
        "status": status,
        "message": message,
        "root_finding_demo": root_demo
    }
