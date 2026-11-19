"""
Numerical methods package for EVolve.
"""
from .interpolation import linear_interpolate, newton_divided_difference, interpolate_missing_readings, NumericalMethodError
from .integration import trapezoidal_rule, simpsons_one_third_rule, compare_integration_methods, estimate_charging_time
from .regression import linear_regression_trip_consumption, predict_driving_range
from .root_finding import bisection_method, newton_raphson_method, solve_journey_feasibility
from .error_analysis import compute_scalar_error, compute_series_error

__all__ = [
    "linear_interpolate",
    "newton_divided_difference",
    "interpolate_missing_readings",
    "trapezoidal_rule",
    "simpsons_one_third_rule",
    "compare_integration_methods",
    "estimate_charging_time",
    "linear_regression_trip_consumption",
    "predict_driving_range",
    "bisection_method",
    "newton_raphson_method",
    "solve_journey_feasibility",
    "compute_scalar_error",
    "compute_series_error",
    "NumericalMethodError"
]
