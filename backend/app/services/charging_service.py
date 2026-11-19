"""
Charging Service for EVolve.
Orchestrates charging session data analysis, energy integration,
interpolation of missing values, time estimation, and error comparison with meter readings.
"""

from typing import List, Dict, Any, Optional
from ..numerical_methods import (
    trapezoidal_rule,
    simpsons_one_third_rule,
    compare_integration_methods,
    interpolate_missing_readings,
    estimate_charging_time,
    compute_scalar_error,
    NumericalMethodError
)


def analyze_charging_readings(
    readings: List[Dict[str, Any]],
    integration_method: str = "trapezoidal",
    meter_reading_kwh: Optional[float] = None
) -> Dict[str, Any]:
    """
    Performs comprehensive analysis on charging readings:
    - Quality checks: detect duplicate timestamps, out-of-order time, negative power, decreasing SoC.
    - Missing value detection: counts missing readings.
    - Energy delivered calculation via Trapezoidal and/or Simpson's rule.
    - Verification against physical meter reading if present.
    - Charging speed / rate diagnostics (average kW, average % per hour).
    """
    if not readings or len(readings) < 2:
        raise NumericalMethodError("At least 2 charging readings are required for analysis.")

    # Sort by elapsed minutes
    sorted_readings = sorted(readings, key=lambda r: float(r["elapsed_minutes"]))
    n = len(sorted_readings)

    data_quality_issues = []
    has_missing_soc = False
    has_missing_power = False

    # Check timestamps and sanity
    for i in range(n - 1):
        t1 = float(sorted_readings[i]["elapsed_minutes"])
        t2 = float(sorted_readings[i+1]["elapsed_minutes"])
        if t2 == t1:
            data_quality_issues.append(f"Duplicate timestamp detected at {t1} minutes.")
        elif t2 < t1:
            data_quality_issues.append(f"Unordered timestamps: {t2} min occurs after {t1} min.")

        soc1 = sorted_readings[i].get("soc_percent")
        soc2 = sorted_readings[i+1].get("soc_percent")

        if soc1 is None or soc2 is None:
            has_missing_soc = True
        elif soc2 < soc1:
            data_quality_issues.append(
                f"Negative charging rate: SoC decreased from {soc1}% (at {t1}m) to {soc2}% (at {t2}m)."
            )

        p1 = sorted_readings[i].get("power_kw")
        if p1 is None:
            has_missing_power = True
        elif p1 < 0:
            data_quality_issues.append(f"Negative charging power detected ({p1} kW at {t1}m).")

    last_p = sorted_readings[-1].get("power_kw")
    if last_p is None:
        has_missing_power = True
    elif last_p < 0:
        data_quality_issues.append(f"Negative charging power detected ({last_p} kW at {sorted_readings[-1]['elapsed_minutes']}m).")

    # Filter valid points with power for integration
    valid_power_points = [
        (float(r["elapsed_minutes"]), float(r["power_kw"]))
        for r in sorted_readings
        if r.get("power_kw") is not None
    ]

    energy_result = None
    comparison_result = None
    if len(valid_power_points) >= 2:
        t_pts = [p[0] for p in valid_power_points]
        p_pts = [p[1] for p in valid_power_points]

        if integration_method.lower() == "simpson":
            try:
                energy_result = simpsons_one_third_rule(t_pts, p_pts)
            except NumericalMethodError as e:
                # Fallback to trapezoid with clear notification
                energy_result = trapezoidal_rule(t_pts, p_pts)
                energy_result["fallback_note"] = f"Simpson's 1/3 could not be applied ({str(e)}). Fell back to Trapezoidal Rule."
        else:
            energy_result = trapezoidal_rule(t_pts, p_pts)

        # Run method comparison
        comparison_result = compare_integration_methods(t_pts, p_pts)

    # Meter error analysis
    meter_error = None
    if meter_reading_kwh is not None and meter_reading_kwh > 0 and energy_result:
        calc_e = energy_result["total_energy_kwh"]
        meter_error = compute_scalar_error(actual=meter_reading_kwh, predicted=calc_e)
        meter_error["note"] = (
            "Difference between charger meter reading and numerical integration of power samples. "
            "Residuals may reflect discrete sampling interval or charger measurement error."
        )

    # Calculate average SoC charging rate (%/hour)
    valid_soc_points = [
        (float(r["elapsed_minutes"]), float(r["soc_percent"]))
        for r in sorted_readings
        if r.get("soc_percent") is not None
    ]
    soc_rate_per_hour = None
    total_soc_gain = None
    if len(valid_soc_points) >= 2:
        s_start = valid_soc_points[0]
        s_end = valid_soc_points[-1]
        dt_hr = (s_end[0] - s_start[0]) / 60.0
        total_soc_gain = s_end[1] - s_start[1]
        if dt_hr > 0:
            soc_rate_per_hour = round(total_soc_gain / dt_hr, 2)

    return {
        "readings_count": n,
        "data_quality_issues": data_quality_issues,
        "has_missing_soc": has_missing_soc,
        "has_missing_power": has_missing_power,
        "total_elapsed_minutes": sorted_readings[-1]["elapsed_minutes"] - sorted_readings[0]["elapsed_minutes"],
        "total_soc_gain_percent": round(total_soc_gain, 2) if total_soc_gain is not None else None,
        "average_soc_rate_per_hour": soc_rate_per_hour,
        "energy_calculation": energy_result,
        "integration_comparison": comparison_result,
        "meter_comparison": meter_error,
        "readings": sorted_readings
    }
