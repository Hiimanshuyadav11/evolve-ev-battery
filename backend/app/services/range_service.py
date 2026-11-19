"""
Range Prediction Service for EVolve.
"""

from typing import List, Dict, Any, Optional
from ..numerical_methods import (
    predict_driving_range,
    linear_regression_trip_consumption,
    NumericalMethodError
)


def compute_range_prediction(
    usable_capacity_kwh: float,
    current_soc_percent: float,
    consumption_kwh_per_km: Optional[float] = None,
    use_trips_regression: bool = False,
    trip_distances_km: Optional[List[float]] = None,
    trip_energies_kwh: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Computes driving range prediction.
    If use_trips_regression is True and historical trips are supplied,
    fits linear regression: Energy = a + b * Distance, using slope b as representative marginal consumption.
    Otherwise uses the direct consumption_kwh_per_km.
    """
    regression_summary = None
    effective_rate = consumption_kwh_per_km

    if use_trips_regression and trip_distances_km and trip_energies_kwh:
        if len(trip_distances_km) >= 2 and len(trip_distances_km) == len(trip_energies_kwh):
            reg = linear_regression_trip_consumption(trip_distances_km, trip_energies_kwh)
            regression_summary = reg
            # Use regression slope if positive, or baseline average
            if reg["slope_kwh_per_km"] > 0:
                effective_rate = reg["slope_kwh_per_km"]
            else:
                effective_rate = reg["baseline_mean_rate_kwh_per_km"]
        else:
            raise NumericalMethodError("At least 2 matching trip distance and energy records required for regression.")

    if effective_rate is None or effective_rate <= 0:
        raise NumericalMethodError(
            "A valid positive energy consumption rate (kWh/km) or trip records are required."
        )

    range_res = predict_driving_range(
        usable_capacity_kwh=usable_capacity_kwh,
        current_soc_percent=current_soc_percent,
        consumption_kwh_per_km=effective_rate
    )

    return {
        "range_prediction": range_res,
        "regression_model": regression_summary,
        "rate_source": "historical_linear_regression" if regression_summary else "entered_consumption"
    }
