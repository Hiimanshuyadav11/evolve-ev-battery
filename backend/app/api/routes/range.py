"""
Range Prediction API routes for EVolve.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ...models.schemas import RangePredictRequest
from ...services.range_service import compute_range_prediction
from ...numerical_methods import NumericalMethodError

router = APIRouter(prefix="/range", tags=["Range"])


@router.post("/predict")
def predict_range(request: RangePredictRequest):
    try:
        return compute_range_prediction(
            usable_capacity_kwh=request.usable_capacity_kwh,
            current_soc_percent=request.current_soc_percent,
            consumption_kwh_per_km=request.consumption_kwh_per_km,
            use_trips_regression=request.use_trips_regression,
            trip_distances_km=request.trip_distances_km,
            trip_energies_kwh=request.trip_energies_kwh
        )
    except NumericalMethodError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error in range prediction: {str(e)}")
