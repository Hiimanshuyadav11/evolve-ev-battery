"""
Battery State of Health (SOH) API routes for EVolve.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from ...data.database import get_connection
from ...models.schemas import BatteryHealthRequest
from ...services.health_service import analyze_battery_health
from ...numerical_methods import NumericalMethodError

router = APIRouter(prefix="/health", tags=["Battery Health"])


@router.get("/measurements")
def list_measurements(profile_id: Optional[int] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if profile_id:
        cursor.execute("SELECT * FROM capacity_measurements WHERE vehicle_profile_id = ? ORDER BY measurement_date ASC", (profile_id,))
    else:
        cursor.execute("SELECT * FROM capacity_measurements ORDER BY measurement_date ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/measurements")
def add_measurement(data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO capacity_measurements (vehicle_profile_id, measurement_date, usable_capacity_kwh, measurement_notes)
        VALUES (?, ?, ?, ?)
    """, (
        data.get("vehicle_profile_id"),
        data.get("measurement_date"),
        data.get("usable_capacity_kwh"),
        data.get("measurement_notes")
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"message": "Capacity measurement recorded", "id": new_id}


@router.post("/analyze")
def estimate_soh(request: BatteryHealthRequest):
    try:
        return analyze_battery_health(
            original_usable_capacity_kwh=request.original_usable_capacity_kwh,
            current_usable_capacity_kwh=request.current_usable_capacity_kwh,
            historical_measurements=request.historical_measurements
        )
    except NumericalMethodError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error in health analysis: {str(e)}")
