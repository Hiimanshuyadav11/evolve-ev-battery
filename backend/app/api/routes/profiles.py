"""
Vehicle Profiles API routes for EVolve.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from ...data.database import get_connection
from ...models.schemas import VehicleProfileCreate, VehicleProfileUpdate, VehicleProfileResponse

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get("", response_model=List[VehicleProfileResponse])
def list_profiles():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicle_profiles ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.post("", response_model=VehicleProfileResponse)
def create_profile(profile: VehicleProfileCreate):
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO vehicle_profiles (name, nominal_capacity_kwh, usable_capacity_kwh, original_usable_capacity_kwh, current_soc, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        profile.name,
        profile.nominal_capacity_kwh,
        profile.usable_capacity_kwh,
        profile.original_usable_capacity_kwh,
        profile.current_soc,
        profile.notes,
        now_iso,
        now_iso
    ))
    new_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM vehicle_profiles WHERE id = ?", (new_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)


@router.get("/{profile_id}", response_model=VehicleProfileResponse)
def get_profile(profile_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicle_profiles WHERE id = ?", (profile_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail=f"Profile with id {profile_id} not found.")
    return dict(row)


@router.put("/{profile_id}", response_model=VehicleProfileResponse)
def update_profile(profile_id: int, updates: VehicleProfileUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicle_profiles WHERE id = ?", (profile_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Profile with id {profile_id} not found.")

    curr = dict(row)
    now_iso = datetime.now().isoformat()

    name = updates.name if updates.name is not None else curr["name"]
    nom = updates.nominal_capacity_kwh if updates.nominal_capacity_kwh is not None else curr["nominal_capacity_kwh"]
    use = updates.usable_capacity_kwh if updates.usable_capacity_kwh is not None else curr["usable_capacity_kwh"]
    orig = updates.original_usable_capacity_kwh if updates.original_usable_capacity_kwh is not None else curr["original_usable_capacity_kwh"]
    soc = updates.current_soc if updates.current_soc is not None else curr["current_soc"]
    notes = updates.notes if updates.notes is not None else curr["notes"]

    cursor.execute("""
        UPDATE vehicle_profiles
        SET name = ?, nominal_capacity_kwh = ?, usable_capacity_kwh = ?, original_usable_capacity_kwh = ?, current_soc = ?, notes = ?, updated_at = ?
        WHERE id = ?
    """, (name, nom, use, orig, soc, notes, now_iso, profile_id))
    conn.commit()

    cursor.execute("SELECT * FROM vehicle_profiles WHERE id = ?", (profile_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return dict(updated_row)


@router.delete("/{profile_id}")
def delete_profile(profile_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM vehicle_profiles WHERE id = ?", (profile_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found.")
    cursor.execute("DELETE FROM vehicle_profiles WHERE id = ?", (profile_id,))
    conn.commit()
    conn.close()
    return {"message": f"Profile {profile_id} deleted successfully."}
