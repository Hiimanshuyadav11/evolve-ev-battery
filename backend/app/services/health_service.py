"""
Battery Health (State of Health - SOH) Service for EVolve.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from ..numerical_methods import NumericalMethodError


def analyze_battery_health(
    original_usable_capacity_kwh: float,
    current_usable_capacity_kwh: float,
    historical_measurements: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Computes State of Health (SOH) and capacity degradation metrics.
    
    Formulas:
    SOH(%) = (C_current / C_original) * 100
    Loss_kwh = C_original - C_current
    Loss(%) = 100 - SOH
    """
    if original_usable_capacity_kwh <= 0:
        raise NumericalMethodError("Original usable capacity must be strictly positive.")
    if current_usable_capacity_kwh <= 0:
        raise NumericalMethodError("Current usable capacity must be strictly positive.")

    warnings = []
    if current_usable_capacity_kwh > original_usable_capacity_kwh:
        warnings.append(
            f"Current measured capacity ({current_usable_capacity_kwh} kWh) exceeds original capacity "
            f"({original_usable_capacity_kwh} kWh). SOH > 100% indicates calibration error or conservative original rating."
        )

    soh_percent = (current_usable_capacity_kwh / original_usable_capacity_kwh) * 100.0
    capacity_loss_kwh = original_usable_capacity_kwh - current_usable_capacity_kwh
    capacity_loss_percent = 100.0 - soh_percent

    # Evaluate warranty / health category
    if soh_percent >= 90.0:
        health_status = "EXCELLENT"
        status_description = "Battery capacity is in optimal condition with minimal degradation."
    elif soh_percent >= 80.0:
        health_status = "GOOD"
        status_description = "Normal operational degradation; within standard manufacturer operating bounds."
    elif soh_percent >= 70.0:
        health_status = "DEGRADED"
        status_description = "Noticeable capacity loss. May trigger OEM battery warranty replacement threshold."
    else:
        health_status = "CRITICAL"
        status_description = "Significant capacity loss. Range will be severely impacted."

    # Historical trend analysis if measurements provided
    trend_data = []
    annual_degradation_rate_percent = None

    if historical_measurements and len(historical_measurements) >= 2:
        # Sort by date
        sorted_m = sorted(historical_measurements, key=lambda m: m.get("date", ""))
        for m in sorted_m:
            cap = float(m.get("capacity_kwh", 0))
            m_soh = (cap / original_usable_capacity_kwh) * 100.0 if original_usable_capacity_kwh > 0 else 0
            trend_data.append({
                "date": m.get("date"),
                "capacity_kwh": cap,
                "soh_percent": round(m_soh, 2),
                "notes": m.get("notes", "")
            })

        # Calculate annualized degradation if dates are parseable
        try:
            d_start = datetime.strptime(sorted_m[0]["date"], "%Y-%m-%d")
            d_end = datetime.strptime(sorted_m[-1]["date"], "%Y-%m-%d")
            days_span = (d_end - d_start).days
            if days_span > 30:
                years_span = days_span / 365.25
                total_loss_pct = trend_data[0]["soh_percent"] - trend_data[-1]["soh_percent"]
                annual_degradation_rate_percent = round(total_loss_pct / years_span, 2)
        except Exception:
            pass

    steps = [
        f"1. Original usable capacity C_orig = {original_usable_capacity_kwh:.2f} kWh",
        f"2. Current measured capacity C_curr = {current_usable_capacity_kwh:.2f} kWh",
        f"3. SOH formula: SOH = (C_curr / C_orig) * 100",
        f"4. Substitution: ({current_usable_capacity_kwh:.2f} / {original_usable_capacity_kwh:.2f}) * 100 = {soh_percent:.2f}%",
        f"5. Capacity Loss: {original_usable_capacity_kwh:.2f} - {current_usable_capacity_kwh:.2f} = {capacity_loss_kwh:.2f} kWh ({capacity_loss_percent:.2f}%)"
    ]

    return {
        "original_usable_capacity_kwh": original_usable_capacity_kwh,
        "current_usable_capacity_kwh": current_usable_capacity_kwh,
        "soh_percent": round(soh_percent, 2),
        "capacity_loss_kwh": round(capacity_loss_kwh, 2),
        "capacity_loss_percent": round(capacity_loss_percent, 2),
        "health_status": health_status,
        "status_description": status_description,
        "annual_degradation_rate_percent": annual_degradation_rate_percent,
        "trend_data": trend_data,
        "warnings": warnings,
        "steps": steps,
        "academic_note": (
            "State of Health (SOH) requires controlled capacity tests (e.g. constant-current full discharge). "
            "It cannot be reliably inferred from a single daily SoC reading or short trip range alone."
        )
    }
