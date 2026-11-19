"""
Numerical Methods Laboratory API routes for EVolve.
Provides worked step-by-step calculations, mathematical derivations,
and method comparisons designed for viva defense and laboratory demonstrations.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List
from ...models.schemas import MethodComparisonRequest
from ...numerical_methods import (
    linear_interpolate,
    newton_divided_difference,
    trapezoidal_rule,
    simpsons_one_third_rule,
    compare_integration_methods,
    linear_regression_trip_consumption,
    bisection_method,
    newton_raphson_method,
    compute_series_error,
    NumericalMethodError
)

router = APIRouter(prefix="/methods", tags=["Methods Lab"])


@router.post("/compare")
def compare_methods(request: MethodComparisonRequest):
    cat = request.category.lower()
    ds = request.dataset

    try:
        if cat == "integration":
            t_min = ds.get("t_minutes", [])
            p_kw = ds.get("power_kw", [])
            return compare_integration_methods(t_min, p_kw)

        elif cat == "interpolation":
            pts = ds.get("points", [])  # list of [x, y]
            target_x = ds.get("target_x")
            if target_x is None:
                raise NumericalMethodError("target_x is required for interpolation comparison.")
            if len(pts) < 2:
                raise NumericalMethodError("At least 2 points required.")

            tuple_pts = [(float(p[0]), float(p[1])) for p in pts]
            
            # Linear using closest two bounding points
            sorted_pts = sorted(tuple_pts, key=lambda p: p[0])
            prev_pts = [p for p in sorted_pts if p[0] <= target_x]
            next_pts = [p for p in sorted_pts if p[0] >= target_x]

            p0 = prev_pts[-1] if prev_pts else sorted_pts[0]
            p1 = next_pts[0] if next_pts and next_pts[0] != p0 else (sorted_pts[1] if len(sorted_pts) > 1 else p0)

            linear_res = linear_interpolate(p0[0], p0[1], p1[0], p1[1], target_x)
            newton_res = newton_divided_difference(tuple_pts, target_x)

            diff = abs(linear_res["result_y"] - newton_res["result_y"])
            return {
                "category": "interpolation",
                "linear": linear_res,
                "newton": newton_res,
                "absolute_difference": round(diff, 6),
                "academic_summary": (
                    "Linear interpolation uses a local 1st-degree polynomial between two adjacent points. "
                    f"Newton divided-difference constructs a single global polynomial of degree {len(pts)-1}. "
                    "For smooth physical battery curves, cubic or low-order polynomials provide higher fidelity, "
                    "while degree > 4 risks Runge's oscillation at boundaries."
                )
            }

        elif cat == "root_finding":
            # Target equation: f(x) = x^2 - target = 0 or custom battery residual function
            f_expr = ds.get("equation_type", "journey_reserve")
            if f_expr == "journey_reserve":
                cu = float(ds.get("usable_capacity_kwh", 60.0))
                dist = float(ds.get("distance_km", 120.0))
                rate = float(ds.get("consumption_kwh_per_km", 0.18))
                reserve_pct = float(ds.get("reserve_percent", 10.0))
                e_req = dist * rate

                def f(s: float) -> float:
                    return (cu * s / 100.0) - e_req - (cu * reserve_pct / 100.0)

                def df(s: float) -> float:
                    return cu / 100.0

                bisect_res = bisection_method(f, 0.0, 100.0, tol=1e-5)
                newton_res = newton_raphson_method(f, df, x0=50.0, tol=1e-5)

                exact_root = round((e_req / cu * 100.0) + reserve_pct, 6)

                return {
                    "category": "root_finding",
                    "exact_analytical_root": exact_root,
                    "bisection": bisect_res,
                    "newton_raphson": newton_res,
                    "iterations_comparison": {
                        "bisection_steps": bisect_res["iterations_count"],
                        "newton_steps": newton_res["iterations_count"],
                        "convergence_rate": "Newton-Raphson achieves quadratic convergence O(e_k^2), requiring significantly fewer iterations than Bisection's linear convergence O(1/2^k)."
                    }
                }
            else:
                raise NumericalMethodError(f"Unsupported equation type '{f_expr}'.")

        else:
            raise NumericalMethodError(f"Unknown comparison category '{cat}'.")

    except NumericalMethodError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Methods Lab calculation error: {str(e)}")


@router.post("/regression-demo")
def regression_demo(data: Dict[str, Any]):
    try:
        distances = data.get("distance_km", [])
        energies = data.get("energy_consumed_kwh", [])
        return linear_regression_trip_consumption(distances, energies)
    except NumericalMethodError as e:
        raise HTTPException(status_code=400, detail=str(e))
