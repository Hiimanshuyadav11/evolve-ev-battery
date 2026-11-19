"""
Database layer for EVolve using SQLite.
Stores vehicle profiles, charging sessions, trip records, capacity measurements, and analysis history.
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "evolve.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initializes all SQLite database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS vehicle_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        nominal_capacity_kwh REAL NOT NULL,
        usable_capacity_kwh REAL NOT NULL,
        original_usable_capacity_kwh REAL NOT NULL,
        current_soc REAL DEFAULT 50.0,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS charging_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_profile_id INTEGER,
        session_name TEXT NOT NULL,
        start_time TEXT,
        data_source TEXT DEFAULT 'manual', -- manual, csv, simulation
        notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (vehicle_profile_id) REFERENCES vehicle_profiles (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS charging_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        charging_session_id INTEGER NOT NULL,
        elapsed_minutes REAL NOT NULL,
        timestamp TEXT,
        soc_percent REAL,
        power_kw REAL,
        cumulative_energy_kwh REAL,
        is_estimated INTEGER DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (charging_session_id) REFERENCES charging_sessions (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS trip_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_profile_id INTEGER,
        trip_date TEXT NOT NULL,
        distance_km REAL NOT NULL,
        energy_consumed_kwh REAL NOT NULL,
        start_soc_percent REAL,
        end_soc_percent REAL,
        data_source TEXT DEFAULT 'manual',
        notes TEXT,
        FOREIGN KEY (vehicle_profile_id) REFERENCES vehicle_profiles (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS capacity_measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_profile_id INTEGER NOT NULL,
        measurement_date TEXT NOT NULL,
        usable_capacity_kwh REAL NOT NULL,
        measurement_notes TEXT,
        FOREIGN KEY (vehicle_profile_id) REFERENCES vehicle_profiles (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS analysis_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_profile_id INTEGER,
        analysis_type TEXT NOT NULL, -- charging, range, trip, health, methods
        title TEXT,
        input_snapshot TEXT NOT NULL,
        result_snapshot TEXT NOT NULL,
        method_used TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (vehicle_profile_id) REFERENCES vehicle_profiles (id) ON DELETE SET NULL
    );
    """)

    conn.commit()
    conn.close()


def seed_synthetic_demo_data(force_reset: bool = False):
    """
    Seeds rich, plausible synthetic demonstration datasets:
    1. Standard EV profile: 'E-Cruiser 60 (Synthetic Demo)'
    2. Regular charging session (constant 11 kW AC charger)
    3. Variable power charging session (DC fast charger showing taper from 50 kW down to 12 kW at high SoC)
    4. Charging session with deliberate missing readings to showcase interpolation
    5. Historical trip logs with distance and kWh consumption for regression
    6. Historical capacity measurements (SOH degradation trend from 60 kWh down to 54.6 kWh over 2 years)
    """
    conn = get_connection()
    cursor = conn.cursor()

    if force_reset:
        cursor.execute("DELETE FROM analysis_records;")
        cursor.execute("DELETE FROM capacity_measurements;")
        cursor.execute("DELETE FROM trip_records;")
        cursor.execute("DELETE FROM charging_readings;")
        cursor.execute("DELETE FROM charging_sessions;")
        cursor.execute("DELETE FROM vehicle_profiles;")
        conn.commit()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM vehicle_profiles")
    if cursor.fetchone()[0] > 0 and not force_reset:
        conn.close()
        return

    now_iso = datetime.now().isoformat()

    # 1. Profile
    cursor.execute("""
        INSERT INTO vehicle_profiles (name, nominal_capacity_kwh, usable_capacity_kwh, original_usable_capacity_kwh, current_soc, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("E-Cruiser 60 (Synthetic Demo)", 64.0, 60.0, 60.0, 52.0, "Demonstration profile for lab viva & computational validation.", now_iso, now_iso))
    profile_id = cursor.lastrowid

    # 2. Charging Session 1: Regular AC 11kW charging (0 to 120 min, step 15 min)
    cursor.execute("""
        INSERT INTO charging_sessions (vehicle_profile_id, session_name, start_time, data_source, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (profile_id, "Session 1: Regular AC 11kW (Uniform Spacing)", "2026-11-15T18:00:00", "simulation", "Uniform 15-minute intervals ideal for Simpson's 1/3 and Trapezoidal comparison.", now_iso))
    sess1_id = cursor.lastrowid

    readings_sess1 = [
        (0.0, 20.0, 11.0, 0.0),
        (15.0, 24.5, 11.0, 2.75),
        (30.0, 29.1, 10.9, 5.48),
        (45.0, 33.7, 11.0, 8.23),
        (60.0, 38.3, 11.0, 10.98),
        (75.0, 42.8, 10.8, 13.70),
        (90.0, 47.4, 11.0, 16.45),
        (105.0, 52.0, 10.9, 19.18),
        (120.0, 56.5, 11.0, 21.93),
    ]
    for el_m, soc, p_kw, c_kwh in readings_sess1:
        cursor.execute("""
            INSERT INTO charging_readings (charging_session_id, elapsed_minutes, timestamp, soc_percent, power_kw, cumulative_energy_kwh, is_estimated)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (sess1_id, el_m, f"2026-11-15T18:{int(el_m):02d}:00", soc, p_kw, c_kwh))

    # 3. Charging Session 2: DC Fast Charge with Power Taper (variable power)
    cursor.execute("""
        INSERT INTO charging_sessions (vehicle_profile_id, session_name, start_time, data_source, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (profile_id, "Session 2: DC Fast Charge with Power Taper", "2026-11-16T10:00:00", "simulation", "Demonstrates fast charging power tapering as battery fills from 15% to 90%.", now_iso))
    sess2_id = cursor.lastrowid

    readings_sess2 = [
        (0.0, 15.0, 50.0, 0.0),
        (10.0, 28.5, 49.5, 8.29),
        (20.0, 42.0, 48.0, 16.42),
        (30.0, 55.0, 45.0, 24.17),
        (40.0, 67.0, 38.0, 31.08),
        (50.0, 77.0, 28.0, 36.58),
        (60.0, 84.0, 18.0, 40.42),
        (70.0, 89.0, 12.0, 42.92),
    ]
    for el_m, soc, p_kw, c_kwh in readings_sess2:
        cursor.execute("""
            INSERT INTO charging_readings (charging_session_id, elapsed_minutes, timestamp, soc_percent, power_kw, cumulative_energy_kwh, is_estimated)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (sess2_id, el_m, f"2026-11-16T10:{int(el_m):02d}:00", soc, p_kw, c_kwh))

    # 4. Charging Session 3: Deliberate Missing Readings (to showcase Interpolation)
    cursor.execute("""
        INSERT INTO charging_sessions (vehicle_profile_id, session_name, start_time, data_source, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (profile_id, "Session 3: Sensor Dropout (Missing Readings)", "2026-11-17T14:00:00", "simulation", "Telemetry dropped at 20 min and 45 min for interpolation demonstration.", now_iso))
    sess3_id = cursor.lastrowid

    readings_sess3 = [
        (0.0, 25.0, 7.2, 0.0, 0),
        (10.0, 28.2, 7.2, 1.2, 0),
        (20.0, None, 7.2, 2.4, 0),  # Missing SoC
        (30.0, 34.6, 7.1, 3.6, 0),
        (45.0, None, 7.2, 5.4, 0),  # Missing SoC
        (60.0, 44.2, 7.2, 7.2, 0),
    ]
    for el_m, soc, p_kw, c_kwh, is_est in readings_sess3:
        cursor.execute("""
            INSERT INTO charging_readings (charging_session_id, elapsed_minutes, timestamp, soc_percent, power_kw, cumulative_energy_kwh, is_estimated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (sess3_id, el_m, f"2026-11-17T14:{int(el_m):02d}:00", soc, p_kw, c_kwh, is_est))

    # 5. Trip Records (10 trips for regression analysis)
    trips_data = [
        ("2026-10-01", 24.5, 4.41, 80.0, 72.6, "City commute (moderate traffic)"),
        ("2026-10-04", 52.0, 9.62, 90.0, 74.0, "Suburban highway commute"),
        ("2026-10-08", 14.2, 2.70, 74.0, 69.5, "Short market run"),
        ("2026-10-12", 85.0, 16.58, 100.0, 72.4, "Intercity highway journey"),
        ("2026-10-17", 36.8, 6.81, 72.0, 60.7, "Mixed ring road trip"),
        ("2026-10-22", 64.0, 12.16, 85.0, 64.7, "Expressway commute"),
        ("2026-10-27", 18.5, 3.52, 65.0, 59.1, "Urban evening drive"),
        ("2026-11-02", 42.0, 7.85, 78.0, 64.9, "Cool weather morning trip"),
        ("2026-11-07", 95.0, 18.53, 95.0, 64.1, "Weekend highway excursion"),
        ("2026-11-12", 30.0, 5.55, 64.0, 54.8, "Normal city loop"),
    ]
    for t_date, dist, kwh, s_soc, e_soc, notes in trips_data:
        cursor.execute("""
            INSERT INTO trip_records (vehicle_profile_id, trip_date, distance_km, energy_consumed_kwh, start_soc_percent, end_soc_percent, data_source, notes)
            VALUES (?, ?, ?, ?, ?, ?, 'simulation', ?)
        """, (profile_id, t_date, dist, kwh, s_soc, e_soc, notes))

    # 6. Capacity Measurements over time (SOH trend)
    cap_data = [
        ("2024-11-15", 60.0, "Factory delivery baseline measurement"),
        ("2025-05-20", 58.8, "6-month checkup (SOH: 98.0%)"),
        ("2025-11-18", 57.6, "1-year annual service (SOH: 96.0%)"),
        ("2026-05-15", 56.1, "18-month inspection (SOH: 93.5%)"),
        ("2026-11-10", 54.9, "2-year checkup (SOH: 91.5%)"),
    ]
    for m_date, cap_kwh, notes in cap_data:
        cursor.execute("""
            INSERT INTO capacity_measurements (vehicle_profile_id, measurement_date, usable_capacity_kwh, measurement_notes)
            VALUES (?, ?, ?, ?)
        """, (profile_id, m_date, cap_kwh, notes))

    conn.commit()
    conn.close()


# Ensure DB initialized on module import
init_db()
seed_synthetic_demo_data(force_reset=False)
