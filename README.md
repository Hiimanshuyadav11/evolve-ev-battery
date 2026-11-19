# EVolve — Intelligent EV Battery Analytics & Predictive System

**Project Category:** B.Tech Second-Year Engineering Project  
**Subject:** Computational Methods Lab  
**Application Type:** Full-Stack Web Application  
**Version:** 1.0.0 (Local SQLite Deployment)

---

## 1. Project Overview

**EVolve** is an engineering computational analytics and decision-support web application that applies classical numerical methods to electric-vehicle (EV) battery and energy data.

Unlike calculators that assume fixed charging speeds or static manufacturer ranges, EVolve processes discrete time-series sensor observations through explainable numerical algorithms:
- **Missing Sensor Telemetry:** Estimated using Linear and Newton's Divided-Difference interpolation.
- **Delivered Charging Energy:** Calculated by integrating time-varying charging power using the Composite Trapezoidal Rule and Simpson's 1/3 Rule.
- **Charging Time Estimation:** Derived by numerically integrating power taper curves $T = \int \frac{C_u/100}{P(S)} dS$.
- **Driving Consumption & Range:** Modeled using Least Squares Linear Regression with Conservative, Expected, and Optimistic scenarios.
- **Journey Feasibility:** Evaluated using Bisection and Newton-Raphson root finding to enforce arrival reserve margins.
- **Battery Health (SOH):** Analyzes usable capacity loss and long-term degradation trends.
- **Methods Lab:** An interactive academic centerpiece displaying step-by-step mathematical substitutions and error metrics ($AE, PE, MAE, RMSE$).

---

## 2. Architecture & Directory Structure

```text
EVolve/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── profiles.py        # Vehicle profile CRUD
│   │   │       ├── charging.py        # Charging analysis & integration
│   │   │       ├── range.py           # Driving range prediction
│   │   │       ├── trips.py           # Journey feasibility & trip logs
│   │   │       ├── health.py          # Battery SOH & capacity tracking
│   │   │       ├── methods.py         # Academic Methods Lab & comparisons
│   │   │       └── data.py            # CSV import/export & demo reset
│   │   ├── core/                      # Configuration & settings
│   │   ├── data/
│   │   │   └── database.py            # SQLite schema & synthetic demo seeder
│   │   ├── models/
│   │   │   └── schemas.py             # Pydantic request & response schemas
│   │   ├── numerical_methods/
│   │   │   ├── interpolation.py       # Linear & Newton polynomial interpolation
│   │   │   ├── integration.py         # Trapezoidal & Simpson's 1/3 rules
│   │   │   ├── regression.py          # Least squares regression & scenarios
│   │   │   ├── root_finding.py        # Bisection & Newton-Raphson solvers
│   │   │   └── error_analysis.py      # AE, PE, MAE, RMSE metrics
│   │   ├── services/
│   │   │   ├── charging_service.py
│   │   │   ├── range_service.py
│   │   │   ├── trip_service.py
│   │   │   └── health_service.py
│   │   └── main.py                    # FastAPI entrypoint & static frontend server
│   ├── tests/
│   │   ├── test_numerical.py          # Known-answer unit tests for algorithms
│   │   └── test_routes_direct.py      # Route integration tests
│   └── requirements.txt
├── frontend/
│   └── dist/
│       ├── index.html                 # Main single-page application console
│       ├── app.js                     # Interactive frontend engine & SVG charts
│       └── styles.css                 # Clean engineering visual stylesheet
├── sample_data/
│   ├── charging_regular_ac11kw.csv    # Uniform 15-min intervals for Simpson 1/3
│   ├── charging_missing_telemetry.csv # Missing telemetry for interpolation demo
│   ├── charging_fast_dc_taper.csv     # 50 kW to 12 kW taper for variable time demo
│   ├── driving_trips_history.csv      # 10 trip records for regression
│   └── battery_capacity_degradation.csv # 2-year capacity measurements for SOH
├── docs/
│   ├── methodology.md                 # Complete mathematical specifications & derivations
│   ├── assumptions_and_limitations.md # System scope, engineering boundaries & physics limits
│   └── viva_notes.md                  # Comprehensive viva voce Q&A preparation guide
├── evolve.db                          # Local SQLite database
└── README.md
```

---

## 3. Quick Start Instructions

### Prerequisites
- Python 3.10+ (tested with Python 3.14)
- Web Browser (Chrome, Edge, Firefox, Safari)

### Installation
1. Navigate to the project backend directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application
Launch the unified FastAPI server (which automatically serves both the API endpoints and the frontend interface):
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser to:
**http://127.0.0.1:8000/**

Interactive API Documentation (Swagger UI):
**http://127.0.0.1:8000/docs**

---

## 4. Running the Automated Test Suite

To run all numerical algorithms and known-answer verification tests:
```bash
python backend/tests/test_numerical.py
```

To run the direct route and API verification tests:
```bash
python backend/tests/test_routes_direct.py
```

All 20 tests execute in less than 0.05 seconds with zero external network dependencies.

---

## 5. Viva Voce Demonstration Sequence (5-Minute Walkthrough)

1. **Overview & Active Profile:**
   - Review current profile: `E-Cruiser 60 (Synthetic Demo)` ($C_u = 60 \text{ kWh}$, $S = 52\%$, available energy = $31.2 \text{ kWh}$).
2. **Missing Sensor Interpolation:**
   - Navigate to **Charging Analysis**.
   - Select `Session 3: Sensor Dropout (Missing Readings)`.
   - Point out missing SoC readings at $t = 20 \text{ min}$ and $t = 45 \text{ min}$.
   - Click **Fill Missing (Interpolation)** to view estimated points and linear slope derivation.
3. **Delivered Energy Numerical Integration:**
   - Select `Session 1: Regular AC 11kW (Uniform Spacing)`.
   - Click **Run Integration**.
   - Show the Trapezoidal strip-by-strip sum ($21.93 \text{ kWh}$) and compare with Simpson's 1/3 Rule ($O(h^4)$ precision).
4. **Charging Time Taper Integration:**
   - Show constant-power baseline vs variable-power curve integration ($T = \int \frac{C_u/100}{P(S)} dS$).
5. **Range Prediction & Least Squares Regression:**
   - Navigate to **Range Prediction**.
   - Click **Calculate Range Prediction** to inspect the fitted equation $E = a + b \cdot d$, $R^2$ goodness-of-fit, and the Conservative/Expected/Optimistic scenario bounds.
6. **Journey Feasibility & Root Finding:**
   - Navigate to **Trip Simulator** and test a 180 km journey.
   - Inspect the arrival SoC and view the iterative **Bisection vs Newton-Raphson** root-finding logs.
7. **Methods Lab Examination:**
   - Open **Methods Lab** to present worked steps, divided-difference tables, and error metrics for evaluation.
