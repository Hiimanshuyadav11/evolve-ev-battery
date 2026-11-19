"""
Main FastAPI Application for EVolve - Intelligent EV Battery Analytics & Predictive System.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .api.routes import profiles, charging, range as range_routes, trips, health, methods, data
from .data.database import init_db, seed_synthetic_demo_data

app = FastAPI(
    title="EVolve - Intelligent EV Battery Analytics & Predictive System",
    description="Computational and numerical methods engine for EV battery analytics, range prediction, and charging optimization.",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to ensure database is initialized
@app.on_event("startup")
def on_startup():
    init_db()
    seed_synthetic_demo_data(force_reset=False)


# Health check endpoint
@app.get("/api/health", tags=["System"])
def system_health_check():
    return {
        "status": "healthy",
        "system": "EVolve Numerical Engine",
        "version": "1.0.0",
        "modules": [
            "Linear & Newton Interpolation",
            "Trapezoidal & Simpson's 1/3 Integration",
            "Least Squares Linear Regression",
            "Bisection & Newton-Raphson Solvers",
            "Battery Health (SOH) Analyzer",
            "Error Analysis (AE, PE, MAE, RMSE)"
        ]
    }


# Include Routers
app.include_router(profiles.router, prefix="/api")
app.include_router(charging.router, prefix="/api")
app.include_router(range_routes.router, prefix="/api")
app.include_router(trips.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(methods.router, prefix="/api")
app.include_router(data.router, prefix="/api")

# Serve frontend build if dist directory exists
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
