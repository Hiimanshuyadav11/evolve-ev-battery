"""
Numerical Methods - Integration Module for EVolve.

Implements:
1. Trapezoidal Rule for discrete (time, power) charging data.
2. Simpson's 1/3 Rule with uniform spacing and even-interval checks.
3. Method comparison (Trapezoidal vs Simpson's).
4. Charging Time Estimation (Constant-power vs Variable-power curve integration).
"""

from typing import List, Tuple, Dict, Any, Optional
import math
from .interpolation import NumericalMethodError, linear_interpolate


def trapezoidal_rule(
    t_minutes: List[float], power_kw: List[float]
) -> Dict[str, Any]:
    """
    Computes energy in kWh by integrating charging power (kW) over time (minutes)
    using the Composite Trapezoidal Rule.
    
    Formula:
        E = sum_{i=0}^{n-1} ((P_i + P_{i+1}) / 2) * (Delta t_hours)
        Delta t_hours = (t_{i+1} - t_i) / 60.0
    """
    n = len(t_minutes)
    if n < 2 or len(power_kw) != n:
        raise NumericalMethodError("At least 2 points of time and power are required for Trapezoidal integration.")

    # Validate timestamps are monotonically increasing
    for i in range(n - 1):
        if t_minutes[i+1] <= t_minutes[i]:
            raise NumericalMethodError(
                f"Timestamps must be strictly increasing. Found t[{i}]={t_minutes[i]} and t[{i+1}]={t_minutes[i+1]}."
            )
        if power_kw[i] < 0:
            raise NumericalMethodError(f"Charging power cannot be negative. Found {power_kw[i]} kW at index {i}.")

    if power_kw[-1] < 0:
        raise NumericalMethodError(f"Charging power cannot be negative. Found {power_kw[-1]} kW at index {n-1}.")

    intervals = []
    total_energy_kwh = 0.0
    cumulative_energy = [0.0]

    for i in range(n - 1):
        dt_min = t_minutes[i+1] - t_minutes[i]
        dt_hr = dt_min / 60.0
        avg_p = (power_kw[i] + power_kw[i+1]) / 2.0
        dE = avg_p * dt_hr
        total_energy_kwh += dE
        cumulative_energy.append(round(total_energy_kwh, 6))

        intervals.append({
            "interval_index": i + 1,
            "t_start_min": t_minutes[i],
            "t_end_min": t_minutes[i+1],
            "dt_minutes": round(dt_min, 4),
            "dt_hours": round(dt_hr, 6),
            "p_start_kw": power_kw[i],
            "p_end_kw": power_kw[i+1],
            "p_avg_kw": round(avg_p, 4),
            "energy_kwh": round(dE, 6),
            "cumulative_kwh": round(total_energy_kwh, 6)
        })

    steps = [
        f"1. Validated {n} points spanning {t_minutes[0]} to {t_minutes[-1]} minutes ({t_minutes[-1] - t_minutes[0]} min total).",
        "2. Applied formula for each subinterval i: dE_i = ((P_i + P_{i+1}) / 2) * (Delta t_i / 60)",
        f"3. Computed sum of {n-1} trapezoidal strips:",
    ]
    for inter in intervals[:5]:  # preview first few in steps
        steps.append(
            f"   - Strip {inter['interval_index']} [{inter['t_start_min']}->{inter['t_end_min']} min]: "
            f"(({inter['p_start_kw']} + {inter['p_end_kw']})/2) * ({inter['dt_minutes']}/60) = {inter['energy_kwh']:.4f} kWh"
        )
    if len(intervals) > 5:
        steps.append(f"   ... ({len(intervals)-5} more intervals summed)")
    steps.append(f"4. Total Delivered Energy E = {total_energy_kwh:.6f} kWh")

    return {
        "method": "Trapezoidal Rule",
        "total_energy_kwh": round(total_energy_kwh, 6),
        "total_time_minutes": round(t_minutes[-1] - t_minutes[0], 4),
        "total_time_hours": round((t_minutes[-1] - t_minutes[0]) / 60.0, 6),
        "average_power_kw": round(total_energy_kwh / (((t_minutes[-1] - t_minutes[0]) / 60.0) or 1.0), 4),
        "interval_count": n - 1,
        "intervals": intervals,
        "cumulative_energy_kwh": cumulative_energy,
        "steps": steps,
        "formula": "E = sum_{i=0}^{n-1} ((P_i + P_{i+1}) / 2) * ((t_{i+1} - t_i) / 60)"
    }


def simpsons_one_third_rule(
    t_minutes: List[float], power_kw: List[float]
) -> Dict[str, Any]:
    """
    Computes energy in kWh using Simpson's 1/3 Rule.
    
    Requirements:
    1. Uniformly spaced time steps: Delta t = h (within tolerance).
    2. Even number of subintervals (m = n - 1 is even, so n is odd).
    
    Formula:
        E = (h_hours / 3) * [ P_0 + P_n + 4 * sum(P_{odd}) + 2 * sum(P_{even}) ]
    """
    n = len(t_minutes)
    if n < 3:
        raise NumericalMethodError("Simpson's 1/3 rule requires at least 3 points (2 subintervals).")
    
    intervals_count = n - 1
    if intervals_count % 2 != 0:
        raise NumericalMethodError(
            f"Simpson's 1/3 rule requires an EVEN number of intervals (ODD number of points). "
            f"Provided dataset has {n} points ({intervals_count} intervals). "
            f"Use Trapezoidal Rule or resample/truncate to an even interval count."
        )

    # Check uniform spacing
    h_min = t_minutes[1] - t_minutes[0]
    if h_min <= 0:
        raise NumericalMethodError("Time interval must be positive and strictly increasing.")

    for i in range(1, intervals_count):
        cur_h = t_minutes[i+1] - t_minutes[i]
        if not math.isclose(cur_h, h_min, rel_tol=1e-3, abs_tol=1e-4):
            raise NumericalMethodError(
                f"Simpson's 1/3 rule requires strictly UNIFORM step sizes. "
                f"Step between point {i} and {i+1} is {cur_h:.4f} min, differing from initial step {h_min:.4f} min. "
                f"Trapezoidal Rule should be used for non-uniform data."
            )

    for p in power_kw:
        if p < 0:
            raise NumericalMethodError(f"Charging power cannot be negative. Found {p} kW.")

    h_hours = h_min / 60.0
    
    # Calculate terms
    p_ends = power_kw[0] + power_kw[-1]
    sum_odd = sum(power_kw[i] for i in range(1, n - 1, 2))
    sum_even = sum(power_kw[i] for i in range(2, n - 1, 2))

    total_energy_kwh = (h_hours / 3.0) * (p_ends + 4.0 * sum_odd + 2.0 * sum_even)

    weights = [1]
    for i in range(1, n - 1):
        weights.append(4 if i % 2 == 1 else 2)
    weights.append(1)

    steps = [
        f"1. Verified uniform spacing h = {h_min:.4f} min ({h_hours:.6f} hours).",
        f"2. Verified {intervals_count} subintervals (even number required for Simpson's 1/3).",
        f"3. Assigned Simpson weights [1, 4, 2, 4, ..., 1]: {weights[:7]}{'...' if len(weights)>7 else ''}",
        f"4. Computed end terms: P_0 + P_{n-1} = {power_kw[0]:.4f} + {power_kw[-1]:.4f} = {p_ends:.4f}",
        f"5. Computed 4 * sum(P_odd): 4 * {sum_odd:.4f} = {4 * sum_odd:.4f}",
        f"6. Computed 2 * sum(P_even): 2 * {sum_even:.4f} = {2 * sum_even:.4f}",
        f"7. Substituted into formula: E = ({h_hours:.6f} / 3) * [{p_ends:.4f} + {4 * sum_odd:.4f} + {2 * sum_even:.4f}]",
        f"8. Final delivered energy = {total_energy_kwh:.6f} kWh"
    ]

    return {
        "method": "Simpson's 1/3 Rule",
        "total_energy_kwh": round(total_energy_kwh, 6),
        "total_time_minutes": round(t_minutes[-1] - t_minutes[0], 4),
        "total_time_hours": round((t_minutes[-1] - t_minutes[0]) / 60.0, 6),
        "step_size_minutes": round(h_min, 4),
        "step_size_hours": round(h_hours, 6),
        "interval_count": intervals_count,
        "weights": weights,
        "steps": steps,
        "formula": "E = (h / 3) * [ P_0 + P_n + 4 * sum(P_odd) + 2 * sum(P_even) ]"
    }


def compare_integration_methods(
    t_minutes: List[float], power_kw: List[float]
) -> Dict[str, Any]:
    """
    Compares Trapezoidal Rule and Simpson's 1/3 Rule on the same dataset.
    Quantifies difference and explains applicability.
    """
    trap_res = trapezoidal_rule(t_minutes, power_kw)
    
    simpson_res = None
    simpson_eligible = True
    simpson_error_reason = ""

    try:
        simpson_res = simpsons_one_third_rule(t_minutes, power_kw)
    except NumericalMethodError as e:
        simpson_eligible = False
        simpson_error_reason = str(e)

    diff_kwh = None
    diff_percent = None

    if simpson_res:
        diff_kwh = abs(trap_res["total_energy_kwh"] - simpson_res["total_energy_kwh"])
        ref = simpson_res["total_energy_kwh"]
        diff_percent = (diff_kwh / ref * 100.0) if ref > 0 else 0.0

    return {
        "trapezoidal": trap_res,
        "simpsons": simpson_res,
        "simpson_eligible": simpson_eligible,
        "simpson_ineligibility_reason": simpson_error_reason,
        "absolute_difference_kwh": round(diff_kwh, 6) if diff_kwh is not None else None,
        "percentage_difference": round(diff_percent, 4) if diff_percent is not None else None,
        "academic_note": (
            "Simpson's 1/3 rule has local truncation error O(h^5) and global error O(h^4), "
            "whereas Trapezoidal rule has global error O(h^2). When uniform spacing is present, "
            "Simpson's rule yields higher precision on parabolic and cubic power curves."
            if simpson_eligible else
            f"Simpson's rule could not be applied: {simpson_error_reason}"
        )
    }


def estimate_charging_time(
    usable_capacity_kwh: float,
    current_soc: float,
    target_soc: float,
    constant_power_kw: Optional[float] = None,
    observed_soc_power_pairs: Optional[List[Tuple[float, float]]] = None
) -> Dict[str, Any]:
    """
    Estimates charging time from current_soc to target_soc.
    
    Methods provided:
    1. Baseline constant-power estimate:
       Delta E = Cu * (target_soc - current_soc) / 100
       T_hours = Delta E / P
    2. Variable-power estimate:
       Integrates T = int_{S0}^{St} (Cu/100) / P(S) dS
       using piecewise linear interpolation of observed charging power taper.
    """
    if usable_capacity_kwh <= 0:
        raise NumericalMethodError("Usable battery capacity must be strictly positive.")
    if not (0.0 <= current_soc <= 100.0):
        raise NumericalMethodError("Current SoC must be between 0% and 100%.")
    if not (0.0 <= target_soc <= 100.0):
        raise NumericalMethodError("Target SoC must be between 0% and 100%.")
    if target_soc <= current_soc:
        raise NumericalMethodError(
            f"Target SoC ({target_soc}%) must be greater than current SoC ({current_soc}%)."
        )

    delta_soc = target_soc - current_soc
    energy_needed_kwh = usable_capacity_kwh * (delta_soc / 100.0)

    # 1. Constant power calculation
    constant_result = None
    if constant_power_kw is not None and constant_power_kw > 0:
        t_hours = energy_needed_kwh / constant_power_kw
        t_minutes = t_hours * 60.0
        hrs_part = int(t_minutes // 60)
        mins_part = int(round(t_minutes % 60))
        if mins_part == 60:
            hrs_part += 1
            mins_part = 0

        constant_result = {
            "method": "Constant-Power Baseline",
            "assumed_power_kw": constant_power_kw,
            "energy_needed_kwh": round(energy_needed_kwh, 4),
            "estimated_hours": round(t_hours, 4),
            "estimated_minutes": round(t_minutes, 1),
            "formatted_time": f"{hrs_part}h {mins_part}m",
            "assumptions_warning": (
                "Idealised estimate: assumes 100% charger efficiency and constant charging rate without taper."
            ),
            "formula": "T = (Cu * (target_soc - current_soc) / 100) / P"
        }

    # 2. Variable power curve calculation
    variable_result = None
    if observed_soc_power_pairs and len(observed_soc_power_pairs) >= 2:
        # Sort by SoC
        pairs = sorted(observed_soc_power_pairs, key=lambda p: p[0])
        soc_vals = [p[0] for p in pairs]
        p_vals = [p[1] for p in pairs]

        # Check positive power
        for p in p_vals:
            if p <= 0:
                raise NumericalMethodError(f"Power readings along taper curve must be positive. Found {p} kW.")

        min_obs_soc, max_obs_soc = min(soc_vals), max(soc_vals)
        warnings = []
        if current_soc < min_obs_soc or target_soc > max_obs_soc:
            warnings.append(
                f"Requested interval [{current_soc}%, {target_soc}%] extends outside observed SoC range "
                f"[{min_obs_soc}%, {max_obs_soc}%]. Boundary extrapolation used."
            )

        # Numerically integrate (Cu / 100) / P(S) from current_soc to target_soc
        # We discretize into small steps of SoC (e.g. 0.5% steps)
        steps_count = max(20, int(delta_soc * 2))
        d_s = delta_soc / steps_count
        
        def get_power_at_s(s: float) -> float:
            if s <= soc_vals[0]:
                return p_vals[0]
            if s >= soc_vals[-1]:
                return p_vals[-1]
            # Find interval
            for i in range(len(soc_vals) - 1):
                if soc_vals[i] <= s <= soc_vals[i+1]:
                    res = linear_interpolate(soc_vals[i], p_vals[i], soc_vals[i+1], p_vals[i+1], s)
                    return max(0.5, res["result_y"])  # clamp positive
            return p_vals[-1]

        # Composite trapezoid over s
        integrated_hours = 0.0
        taper_curve_points = []
        for i in range(steps_count):
            s_a = current_soc + i * d_s
            s_b = current_soc + (i + 1) * d_s
            p_a = get_power_at_s(s_a)
            p_b = get_power_at_s(s_b)
            # integrand is (Cu / 100) / P(s)
            val_a = (usable_capacity_kwh / 100.0) / p_a
            val_b = (usable_capacity_kwh / 100.0) / p_b
            integrated_hours += ((val_a + val_b) / 2.0) * d_s

            if i % max(1, steps_count // 10) == 0:
                taper_curve_points.append({"soc": round(s_a, 2), "power_kw": round(p_a, 2)})
        taper_curve_points.append({"soc": round(target_soc, 2), "power_kw": round(get_power_at_s(target_soc), 2)})

        v_mins = integrated_hours * 60.0
        v_h_part = int(v_mins // 60)
        v_m_part = int(round(v_mins % 60))
        if v_m_part == 60:
            v_h_part += 1
            v_m_part = 0

        variable_result = {
            "method": "Variable-Power Curve Integration",
            "energy_needed_kwh": round(energy_needed_kwh, 4),
            "estimated_hours": round(integrated_hours, 4),
            "estimated_minutes": round(v_mins, 1),
            "formatted_time": f"{v_h_part}h {v_m_part}m",
            "warnings": warnings,
            "taper_curve_preview": taper_curve_points,
            "formula": "T = int_{S0}^{St} ((Cu / 100) / P(S)) dS",
            "explanation": (
                "Takes into account power taper at higher battery percentages (e.g. above 80%), "
                "yielding a more realistic estimation than constant power."
            )
        }

    return {
        "current_soc": current_soc,
        "target_soc": target_soc,
        "usable_capacity_kwh": usable_capacity_kwh,
        "energy_needed_kwh": round(energy_needed_kwh, 4),
        "constant_power_estimate": constant_result,
        "variable_power_estimate": variable_result
    }
