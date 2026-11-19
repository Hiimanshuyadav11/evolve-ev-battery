"""
Numerical Methods - Error Analysis Module for EVolve.

Implements:
1. Absolute Error (AE)
2. Relative Percentage Error (PE)
3. Mean Absolute Error (MAE)
4. Root Mean Squared Error (RMSE)
5. Comparative method error analysis against reference measurements.
"""

from typing import List, Dict, Any, Optional
import math
from .interpolation import NumericalMethodError


def compute_scalar_error(actual: float, predicted: float) -> Dict[str, Any]:
    """
    Computes absolute and relative percentage error for a single scalar pair.
    """
    ae = abs(actual - predicted)
    pe = None
    pe_str = "N/A (actual is zero)"

    if not math.isclose(actual, 0.0, abs_tol=1e-12):
        pe = (ae / abs(actual)) * 100.0
        pe_str = f"{pe:.4f}%"

    return {
        "actual": actual,
        "predicted": predicted,
        "absolute_error": round(ae, 6),
        "percentage_error": round(pe, 4) if pe is not None else None,
        "percentage_error_display": pe_str
    }


def compute_series_error(
    actual_values: List[float], predicted_values: List[float]
) -> Dict[str, Any]:
    """
    Computes series error metrics:
    - MAE: Mean Absolute Error
    - RMSE: Root Mean Squared Error
    - Mean Percentage Error (where defined)
    - Itemized error breakdown
    """
    n = len(actual_values)
    if n == 0 or len(predicted_values) != n:
        raise NumericalMethodError("Actual and predicted series must be non-empty and of identical length.")

    itemized = []
    abs_errors = []
    sq_errors = []
    valid_pe_list = []

    for i in range(n):
        act = actual_values[i]
        pred = predicted_values[i]
        err = compute_scalar_error(act, pred)
        abs_errors.append(err["absolute_error"])
        sq_errors.append((act - pred) ** 2)
        if err["percentage_error"] is not None:
            valid_pe_list.append(err["percentage_error"])

        itemized.append({
            "index": i + 1,
            "actual": act,
            "predicted": pred,
            "absolute_error": err["absolute_error"],
            "percentage_error": err["percentage_error"]
        })

    mae = sum(abs_errors) / n
    rmse = math.sqrt(sum(sq_errors) / n)
    mape = (sum(valid_pe_list) / len(valid_pe_list)) if valid_pe_list else None

    return {
        "count": n,
        "mae": round(mae, 6),
        "rmse": round(rmse, 6),
        "mape": round(mape, 4) if mape is not None else None,
        "itemized": itemized,
        "formulas": {
            "MAE": "sum(|y_i - y_hat_i|) / n",
            "RMSE": "sqrt(sum((y_i - y_hat_i)^2) / n)",
            "PE": "(|y - y_hat| / |y|) * 100"
        }
    }
