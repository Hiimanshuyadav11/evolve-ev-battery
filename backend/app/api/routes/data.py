"""
Data & History API routes for EVolve.
Handles CSV import, CSV export, analysis snapshot persistence, and demo-data reset.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import Response
from typing import List, Dict, Any, Optional
import csv
import io
import json
from datetime import datetime
from ...data.database import get_connection, seed_synthetic_demo_data
from ...models.schemas import AnalysisRecordCreate, AnalysisRecordResponse

router = APIRouter(prefix="/data", tags=["Data & History"])


@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    dataset_type: str = Form(..., description="'charging', 'trips', or 'capacity'"),
    profile_id: Optional[int] = Form(None)
):
    """
    Parses uploaded CSV and imports into SQLite database.
    Supported types:
    - charging: timestamp, elapsed_minutes, soc_percent, power_kw, cumulative_energy_kwh
    - trips: trip_date, distance_km, energy_consumed_kwh, start_soc, end_soc, notes
    - capacity: measurement_date, usable_capacity_kwh, measurement_notes
    """
    content = await file.read()
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            decoded = content.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=400, detail="Unable to decode file. Please upload a valid UTF-8 CSV.")

    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file is empty or has no header row.")

    # Clean fieldnames
    cleaned_fields = [f.strip().lower() for f in reader.fieldnames if f]

    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()
    imported_count = 0

    try:
        if dataset_type == "charging":
            cursor.execute("""
                INSERT INTO charging_sessions (vehicle_profile_id, session_name, start_time, data_source, notes, created_at)
                VALUES (?, ?, ?, 'csv', ?, ?)
            """, (profile_id, f"Imported: {file.filename}", now_iso, "Imported via CSV upload", now_iso))
            session_id = cursor.lastrowid

            for row in reader:
                # Find elapsed_minutes or compute from row index
                clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k and v is not None}
                el_min_str = clean_row.get("elapsed_minutes") or clean_row.get("elapsed_min") or clean_row.get("time_min")
                el_min = float(el_min_str) if el_min_str else float(imported_count * 5.0)

                soc_str = clean_row.get("soc_percent") or clean_row.get("soc")
                soc = float(soc_str) if (soc_str and soc_str.lower() != "nan" and soc_str != "") else None

                p_str = clean_row.get("power_kw") or clean_row.get("power")
                power = float(p_str) if (p_str and p_str.lower() != "nan" and p_str != "") else None

                cum_str = clean_row.get("cumulative_energy_kwh") or clean_row.get("energy_kwh")
                cum = float(cum_str) if (cum_str and cum_str.lower() != "nan" and cum_str != "") else None

                ts = clean_row.get("timestamp") or f"T+{int(el_min)}m"

                cursor.execute("""
                    INSERT INTO charging_readings (charging_session_id, elapsed_minutes, timestamp, soc_percent, power_kw, cumulative_energy_kwh, is_estimated)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (session_id, el_min, ts, soc, power, cum))
                imported_count += 1

            conn.commit()
            return {"message": f"Successfully imported {imported_count} charging readings", "session_id": session_id}

        elif dataset_type == "trips":
            for row in reader:
                clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k and v is not None}
                t_date = clean_row.get("trip_date") or clean_row.get("date") or datetime.now().strftime("%Y-%m-%d")
                dist = float(clean_row.get("distance_km") or clean_row.get("distance") or 0.0)
                kwh = float(clean_row.get("energy_consumed_kwh") or clean_row.get("energy_kwh") or 0.0)
                s_soc = float(clean_row.get("start_soc_percent") or clean_row.get("start_soc")) if clean_row.get("start_soc_percent") or clean_row.get("start_soc") else None
                e_soc = float(clean_row.get("end_soc_percent") or clean_row.get("end_soc")) if clean_row.get("end_soc_percent") or clean_row.get("end_soc") else None
                notes = clean_row.get("notes") or ""

                if dist > 0:
                    cursor.execute("""
                        INSERT INTO trip_records (vehicle_profile_id, trip_date, distance_km, energy_consumed_kwh, start_soc_percent, end_soc_percent, data_source, notes)
                        VALUES (?, ?, ?, ?, ?, ?, 'csv', ?)
                    """, (profile_id, t_date, dist, kwh, s_soc, e_soc, notes))
                    imported_count += 1

            conn.commit()
            return {"message": f"Successfully imported {imported_count} trip records"}

        elif dataset_type == "capacity":
            for row in reader:
                clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k and v is not None}
                m_date = clean_row.get("measurement_date") or clean_row.get("date") or datetime.now().strftime("%Y-%m-%d")
                cap = float(clean_row.get("usable_capacity_kwh") or clean_row.get("capacity_kwh") or 0.0)
                notes = clean_row.get("measurement_notes") or clean_row.get("notes") or ""

                if cap > 0 and profile_id:
                    cursor.execute("""
                        INSERT INTO capacity_measurements (vehicle_profile_id, measurement_date, usable_capacity_kwh, measurement_notes)
                        VALUES (?, ?, ?, ?)
                    """, (profile_id, m_date, cap, notes))
                    imported_count += 1

            conn.commit()
            return {"message": f"Successfully imported {imported_count} capacity measurements"}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown dataset_type '{dataset_type}'.")

    except ValueError as ve:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Data parsing error: {str(ve)}")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    finally:
        conn.close()


@router.get("/export-csv/{dataset_type}")
def export_csv(dataset_type: str, session_id: Optional[int] = None, profile_id: Optional[int] = None):
    conn = get_connection()
    cursor = conn.cursor()
    output = io.StringIO()
    writer = csv.writer(output)

    if dataset_type == "charging":
        writer.writerow(["elapsed_minutes", "timestamp", "soc_percent", "power_kw", "cumulative_energy_kwh", "is_estimated", "notes"])
        if session_id:
            cursor.execute("SELECT elapsed_minutes, timestamp, soc_percent, power_kw, cumulative_energy_kwh, is_estimated, notes FROM charging_readings WHERE charging_session_id = ? ORDER BY elapsed_minutes ASC", (session_id,))
        else:
            cursor.execute("SELECT elapsed_minutes, timestamp, soc_percent, power_kw, cumulative_energy_kwh, is_estimated, notes FROM charging_readings ORDER BY id ASC")
        for row in cursor.fetchall():
            writer.writerow(list(row))
        filename = f"evolve_charging_{session_id or 'all'}.csv"

    elif dataset_type == "trips":
        writer.writerow(["trip_date", "distance_km", "energy_consumed_kwh", "start_soc_percent", "end_soc_percent", "data_source", "notes"])
        if profile_id:
            cursor.execute("SELECT trip_date, distance_km, energy_consumed_kwh, start_soc_percent, end_soc_percent, data_source, notes FROM trip_records WHERE vehicle_profile_id = ? ORDER BY trip_date ASC", (profile_id,))
        else:
            cursor.execute("SELECT trip_date, distance_km, energy_consumed_kwh, start_soc_percent, end_soc_percent, data_source, notes FROM trip_records ORDER BY trip_date ASC")
        for row in cursor.fetchall():
            writer.writerow(list(row))
        filename = "evolve_trips.csv"

    elif dataset_type == "capacity":
        writer.writerow(["measurement_date", "usable_capacity_kwh", "measurement_notes"])
        cursor.execute("SELECT measurement_date, usable_capacity_kwh, measurement_notes FROM capacity_measurements ORDER BY measurement_date ASC")
        for row in cursor.fetchall():
            writer.writerow(list(row))
        filename = "evolve_capacity.csv"

    else:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Unsupported export dataset_type '{dataset_type}'.")

    conn.close()
    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/history")
def list_analysis_history(analysis_type: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if analysis_type:
        cursor.execute("SELECT * FROM analysis_records WHERE analysis_type = ? ORDER BY id DESC", (analysis_type,))
    else:
        cursor.execute("SELECT * FROM analysis_records ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["input_snapshot"] = json.loads(d["input_snapshot"])
        d["result_snapshot"] = json.loads(d["result_snapshot"])
        result.append(d)
    return result


@router.post("/history")
def save_analysis_history(record: AnalysisRecordCreate):
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO analysis_records (vehicle_profile_id, analysis_type, title, input_snapshot, result_snapshot, method_used, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        record.vehicle_profile_id,
        record.analysis_type,
        record.title,
        json.dumps(record.input_snapshot),
        json.dumps(record.result_snapshot),
        record.method_used,
        now_iso
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"message": "Analysis snapshot saved", "id": new_id}


@router.post("/reset-demo-data")
def reset_demo():
    seed_synthetic_demo_data(force_reset=True)
    return {"message": "All database tables reset and seeded with fresh Synthetic Demonstration Data."}
