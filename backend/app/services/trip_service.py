"""
Trip Feasibility & Simulation Service for EVolve.
"""

from typing import Dict, Any, Optional
from ..numerical_methods import solve_journey_feasibility


def simulate_trip(
    usable_capacity_kwh: float,
    starting_soc_percent: float,
    journey_distance_km: float,
    consumption_rate_kwh_per_km: float,
    desired_reserve_percent: float = 10.0
) -> Dict[str, Any]:
    """
    Evaluates trip feasibility, battery depletion, arrival SoC,
    and demonstrates root-finding solvers (Bisection & Newton-Raphson).
    """
    return solve_journey_feasibility(
        usable_capacity_kwh=usable_capacity_kwh,
        starting_soc_percent=starting_soc_percent,
        journey_distance_km=journey_distance_km,
        consumption_rate_kwh_per_km=consumption_rate_kwh_per_km,
        desired_reserve_percent=desired_reserve_percent,
        use_root_finding_demo=True
    )
