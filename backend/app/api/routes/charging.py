"""
Charging Analysis API routes for EVolve.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
from ...data.database import get_connection
from ...models.schemas import (
    ChargingSessionCreate,
    ChargingSessionResponse,
    InterpolateRequest,
    EnergyCalculationRequest,
    ChargingTimeEstimateRequest
)
from ...services.charging_service import analyze_charging_readings
from ...numerical_methods import (
    interpolate_missing_readings,
    trapezoidal_rule,
    simpsons_one_third_rule,
    estimate_charging_time,
    NumericalMethodError
)

router = APIRouter(prefix="/charging", tags=["Charging"])


@router.post("/analyze")
def analyze_readings(
    readings: List[Dict[str, Any]],
    method: str = Query("trapezoidal", description="'trapezoidal' or 'simpson'"),
    meter_reading_kwh: Optional[float] = Query(None, description="Optional physical meter reading to evaluate error")
):
    try:
        return analyze_charging_readings(readings, integration_method=method, meter_reading_kwh=meter_reading_kwh)
    except NumericalMethodError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error in charging analysis: {str(e)}")


@router.post("/interpolate")
def interpolate_readings(request: InterpolateRequest):
    try:
        raw_list = [r.model_dump() for r in request.readings]
        return interpolate_missing_readings(raw_list, method=request.method, max_gap_minutes=request.max_gap_minutes)
    except NumericalMethodError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/energy")
def calculate_energy(request: EnergyCalculationRequest):
    try:
        if request.method.lower() == "simpson":
            return simpsons_one_third_rule(request.t_minutes, request.power_kw)
        return trapezoidal_rule(request.t_minutes, request.power_kw)
    except NumericalMethodError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/time-estimate")
def get_charging_time_estimate(request: ChargingTimeEstimateRequest):
    try:
        pairs = None
        if request.observed_soc_power_pairs:
            pairs = [(float(p[0]), float(p[1])) for p in request.observed_soc_power_pairs]

        return estimate_charging_time(
            usable_capacity_kwh=request.usable_capacity_kwh,
            current_soc=request.current_soc,
            target_soc=request.target_soc,
            constant_power_kw=request.constant_power_kw,
            observed_soc_power_pairs=pairs
        )
    except NumericalMethodError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions")
def list_sessions(profile_id: Optional[int] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if profile_id:
        cursor.execute("SELECT * FROM charging_sessions WHERE vehicle_profile_id = ? ORDER BY id DESC", (profile_id,))
    else:
        cursor.execute("SELECT * FROM charging_sessions ORDER BY id DESC")
    sessions = [dict(r) for r in cursor.fetchall()]

    # Fetch readings for each
    for s in sessions:
        cursor.execute("""
            SELECT elapsed_minutes, timestamp, soc_percent, power_kw, cumulative_energy_kwh, is_estimated, notes
            FROM charging_readings WHERE charging_session_id = ? ORDER BY elapsed_minutes ASC
        """, (s["id"],))
        s["readings"] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return sessions


@router.post("/sessions")
def save_session(session_data: ChargingSessionCreate):
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()
    start_t = session_data.start_time or now_iso

    cursor.execute("""
        INSERT INTO charging_sessions (vehicle_profile_id, session_name, start_time, data_source, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        session_data.vehicle_profile_id,
        session_data.session_name,
        start_t,
        session_data.data_source,
        session_data.notes,
        now_iso
    ))
    session_id = cursor.lastrowid

    for r in session_data.readings:
        cursor.execute("""
            INSERT INTO charging_readings (charging_session_id, elapsed_minutes, timestamp, soc_percent, power_kw, cumulative_energy_kwh, is_estimated, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            r.elapsed_minutes,
            r.timestamp or f"T+{int(r.elapsed_minutes)}m",
            r.soc_percent,
            r.power_kw,
            r.cumulative_energy_kwh,
            1 if r.is_estimated else 0,
            r.notes
        ))

    conn.commit()
    conn.close()
    return {"message": "Session saved successfully", "session_id": session_id}
