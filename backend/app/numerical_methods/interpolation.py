"""
Numerical Methods - Interpolation Module for EVolve.

Implements:
1. Linear Interpolation with step-by-step derivation.
2. Newton Divided-Difference Polynomial Interpolation.
3. Series Interpolation for missing values with gap & boundary checks.
"""

from typing import List, Tuple, Dict, Any, Optional
import math


class NumericalMethodError(ValueError):
    """Custom exception for numerical calculation errors."""
    pass


def linear_interpolate(
    x0: float, y0: float, x1: float, y1: float, x: float
) -> Dict[str, Any]:
    """
    Computes linear interpolation between two points (x0, y0) and (x1, y1) at target x.
    Formula: y(x) = y0 + ((x - x0) / (x1 - x0)) * (y1 - y0)
    
    Returns:
        Dict with result, slope, formula, step-by-step substitution, and warnings.
    """
    if math.isclose(x0, x1, abs_tol=1e-9):
        raise NumericalMethodError(f"Duplicate x values detected (x0={x0}, x1={x1}). Division by zero is undefined.")
    
    warnings = []
    # Check if target is extrapolation
    min_x, max_x = min(x0, x1), max(x0, x1)
    if x < min_x or x > max_x:
        warnings.append(f"Target x={x} is outside the interval [{min_x}, {max_x}]. Extrapolation is active.")

    slope = (y1 - y0) / (x1 - x0)
    dx = x - x0
    y = y0 + slope * dx

    steps = [
        f"1. Identify points: (x0, y0) = ({x0}, {y0}), (x1, y1) = ({x1}, {y1}), target x = {x}",
        f"2. Check interval: x in [{min_x}, {max_x}] -> {'Valid interpolation' if not warnings else 'Extrapolation warning'}",
        f"3. Compute slope m = (y1 - y0) / (x1 - x0) = ({y1} - {y0}) / ({x1} - {x0}) = {slope:.6f}",
        f"4. Apply linear equation: y(x) = y0 + m * (x - x0)",
        f"5. Substitute: y({x}) = {y0} + ({slope:.6f}) * ({x} - {x0})",
        f"6. Final calculated value = {y:.6f}"
    ]

    return {
        "method": "Linear Interpolation",
        "target_x": x,
        "result_y": round(y, 6),
        "slope": round(slope, 6),
        "formula": "y(x) = y0 + ((x - x0) / (x1 - x0)) * (y1 - y0)",
        "steps": steps,
        "warnings": warnings,
        "points_used": [{"x": x0, "y": y0}, {"x": x1, "y": y1}]
    }


def newton_divided_difference(
    points: List[Tuple[float, float]], x: float
) -> Dict[str, Any]:
    """
    Computes Newton's Divided-Difference polynomial interpolation for a set of points at target x.
    P_n(x) = f[x0] + sum_{k=1}^n f[x0,...,xk] * prod_{j=0}^{k-1} (x - xj)
    
    Returns:
        Dict with result, divided difference table, basis terms, polynomial expression, and steps.
    """
    n = len(points)
    if n < 2:
        raise NumericalMethodError("At least 2 distinct points are required for Newton interpolation.")
    
    # Sort points by x
    sorted_pts = sorted(points, key=lambda p: p[0])
    xs = [p[0] for p in sorted_pts]
    ys = [p[1] for p in sorted_pts]

    # Validate distinct x coordinates
    for i in range(len(xs) - 1):
        if math.isclose(xs[i], xs[i+1], abs_tol=1e-9):
            raise NumericalMethodError(f"Duplicate x values detected at x={xs[i]}. Points must have distinct x coordinates.")

    warnings = []
    min_x, max_x = min(xs), max(xs)
    if x < min_x or x > max_x:
        warnings.append(f"Target x={x} is outside domain [{min_x}, {max_x}]. Polynomial extrapolation may lead to large error.")
    if n > 5:
        warnings.append(f"Polynomial degree is {n-1} (>4). High-degree polynomials are prone to Runge's phenomenon / oscillation.")

    # Initialize divided difference table: n x n
    dd_table = [[0.0] * n for _ in range(n)]
    for i in range(n):
        dd_table[i][0] = ys[i]

    for j in range(1, n):
        for i in range(n - j):
            denom = xs[i + j] - xs[i]
            dd_table[i][j] = (dd_table[i + 1][j - 1] - dd_table[i][j - 1]) / denom

    coefficients = [dd_table[0][j] for j in range(n)]

    # Evaluate polynomial at target x
    result = coefficients[0]
    term_product = 1.0
    terms_breakdown = [f"f[x0] = {coefficients[0]:.6f}"]
    poly_terms = [f"{coefficients[0]:.4f}"]

    for k in range(1, n):
        term_product *= (x - xs[k - 1])
        term_val = coefficients[k] * term_product
        result += term_val
        factors_str = "".join([f"(x - {xs[j]:.2f})" for j in range(k)])
        poly_terms.append(f"({coefficients[k]:+.4f}){factors_str}")
        terms_breakdown.append(
            f"Term {k}: f[x0..x{k}] * prod(x-xj) = ({coefficients[k]:.6f}) * ({term_product:.6f}) = {term_val:.6f}"
        )

    # Human-readable table representation
    table_representation = []
    for i in range(n):
        row = {
            "x": xs[i],
            "f[x]": round(dd_table[i][0], 6)
        }
        for j in range(1, n - i):
            row[f"order_{j}"] = round(dd_table[i][j], 6)
        table_representation.append(row)

    steps = [
        f"1. Ordered {n} distinct points: {list(zip(xs, ys))}",
        f"2. Constructed divided-difference pyramid table of order 0 to {n-1}",
        f"3. Extracted leading diagonal coefficients: {[round(c, 6) for c in coefficients]}",
        f"4. Polynomial formulation: P(x) = " + " + ".join(poly_terms),
        f"5. Substituted x = {x}:",
    ] + terms_breakdown + [f"6. Summed all polynomial terms -> P({x}) = {result:.6f}"]

    return {
        "method": "Newton Divided-Difference",
        "target_x": x,
        "result_y": round(result, 6),
        "degree": n - 1,
        "coefficients": [round(c, 6) for c in coefficients],
        "polynomial_str": " + ".join(poly_terms),
        "steps": steps,
        "warnings": warnings,
        "dd_table": table_representation,
        "points_used": [{"x": p[0], "y": p[1]} for p in sorted_pts]
    }


def interpolate_missing_readings(
    readings: List[Dict[str, Any]],
    method: str = "linear",
    max_gap_minutes: float = 30.0
) -> Dict[str, Any]:
    """
    Detects and fills missing SoC or Power readings in a time-series table.
    
    Each reading is expected to have 'elapsed_minutes' and 'soc_percent'.
    A missing value can be represented by None or NaN in 'soc_percent'.
    
    Validations:
    - Readings must be sorted by elapsed_minutes.
    - Warn if missing reading spans a gap > max_gap_minutes.
    - Do not extrapolate boundary missing readings (first or last) without explicit flagging.
    """
    if not readings:
        return {"readings": [], "estimated_count": 0, "logs": ["Dataset is empty."]}

    # Validate sorting and timestamps
    sorted_readings = sorted(readings, key=lambda r: r.get("elapsed_minutes", 0))
    for i in range(len(sorted_readings) - 1):
        if sorted_readings[i]["elapsed_minutes"] == sorted_readings[i+1]["elapsed_minutes"]:
            raise NumericalMethodError(f"Duplicate timestamp found at {sorted_readings[i]['elapsed_minutes']} minutes.")

    # Collect known points for soc_percent
    known_soc = []
    for r in sorted_readings:
        soc = r.get("soc_percent")
        if soc is not None and not (isinstance(soc, float) and math.isnan(soc)):
            known_soc.append((float(r["elapsed_minutes"]), float(soc)))

    if len(known_soc) < 2:
        raise NumericalMethodError("At least 2 known SoC readings are required to interpolate missing values.")

    output_readings = []
    logs = []
    estimated_count = 0

    for r in sorted_readings:
        row = dict(r)
        t = float(r["elapsed_minutes"])
        soc = r.get("soc_percent")
        is_missing = soc is None or (isinstance(soc, float) and math.isnan(soc))

        if is_missing:
            # Find bounding points
            prev_pts = [p for p in known_soc if p[0] < t]
            next_pts = [p for p in known_soc if p[0] > t]

            if not prev_pts or not next_pts:
                row["is_estimated"] = False
                row["estimation_note"] = "Boundary point: cannot interpolate without extrapolation."
                logs.append(f"Time {t} min is at the dataset boundary. Cannot interpolate.")
            else:
                p0 = prev_pts[-1]
                p1 = next_pts[0]
                gap = p1[0] - p0[0]
                gap_warn = f" (Warning: large time gap of {gap} min)" if gap > max_gap_minutes else ""

                if method.lower() == "newton" and len(known_soc) >= 3:
                    # Use closest 3 or 4 points to avoid high-degree Runge oscillation
                    closest = sorted(known_soc, key=lambda p: abs(p[0] - t))[:min(4, len(known_soc))]
                    res = newton_divided_difference(closest, t)
                    est_val = res["result_y"]
                    row["soc_percent"] = est_val
                    row["is_estimated"] = True
                    row["estimation_note"] = f"Estimated via Newton Polynomial using {len(closest)} nearby points{gap_warn}"
                else:
                    res = linear_interpolate(p0[0], p0[1], p1[0], p1[1], t)
                    est_val = res["result_y"]
                    row["soc_percent"] = est_val
                    row["is_estimated"] = True
                    row["estimation_note"] = f"Estimated via Linear Interpolation between t={p0[0]} and t={p1[0]}{gap_warn}"

                estimated_count += 1
                logs.append(f"Filled SoC at {t} min = {est_val:.2f}%{gap_warn}")
        else:
            row["is_estimated"] = bool(row.get("is_estimated", False))

        output_readings.append(row)

    return {
        "readings": output_readings,
        "estimated_count": estimated_count,
        "method_used": method,
        "logs": logs
    }
