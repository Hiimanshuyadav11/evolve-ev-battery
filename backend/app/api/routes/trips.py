"""
Trips and Journey Feasibility API routes for EVolve.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from ...data.database import get_connection
from ...models.schemas import TripFeasibilityRequest
from ...services.trip_service import simulate_trip
from ...numerical_methods import NumericalMethodError

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.get("")
def list_trips(profile_id: Optional[int] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if profile_id:
        cursor.execute("SELECT * FROM trip_records WHERE vehicle_profile_id = ? ORDER BY trip_date DESC, id DESC", (profile_id,))
    else:
        cursor.execute("SELECT * FROM trip_records ORDER BY trip_date DESC, id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("")
def create_trip(trip: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trip_records (vehicle_profile_id, trip_date, distance_km, energy_consumed_kwh, start_soc_percent, end_soc_percent, data_source, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trip.get("vehicle_profile_id"),
        trip.get("trip_date"),
        trip.get("distance_km"),
        trip.get("energy_consumed_kwh"),
        trip.get("start_soc_percent"),
        trip.get("end_soc_percent"),
        trip.get("data_source", "manual"),
        trip.get("notes")
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"message": "Trip created successfully", "id": new_id}


@router.post("/analyze")
def analyze_trip_feasibility(request: TripFeasibilityRequest):
    try:
        return simulate_trip(
            usable_capacity_kwh=request.usable_capacity_kwh,
            starting_soc_percent=request.starting_soc_percent,
            journey_distance_km=request.journey_distance_km,
            consumption_rate_kwh_per_km=request.consumption_rate_kwh_per_km,
            desired_reserve_percent=request.desired_reserve_percent
        )
    except NumericalMethodError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error in trip analysis: {str(e)}")
