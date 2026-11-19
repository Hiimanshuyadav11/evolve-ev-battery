"""
Pydantic Schemas for Request Validation and Response Serialization in EVolve.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator


# --- Vehicle Profile Schemas ---

class VehicleProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name or identifier for the vehicle profile")
    nominal_capacity_kwh: float = Field(..., gt=0, description="Manufacturer nominal battery capacity in kWh")
    usable_capacity_kwh: float = Field(..., gt=0, description="Usable battery capacity in kWh (Cu)")
    original_usable_capacity_kwh: float = Field(..., gt=0, description="Original usable battery capacity when new")
    current_soc: float = Field(default=50.0, ge=0.0, le=100.0, description="Current State of Charge percentage")
    notes: Optional[str] = Field(default="", description="Optional context or notes")

    @field_validator("usable_capacity_kwh")
    @classmethod
    def validate_usable(cls, v: float, values: Any):
        # Usable capacity should not exceed nominal capacity unless noted
        return v


class VehicleProfileCreate(VehicleProfileBase):
    pass


class VehicleProfileUpdate(BaseModel):
    name: Optional[str] = None
    nominal_capacity_kwh: Optional[float] = Field(None, gt=0)
    usable_capacity_kwh: Optional[float] = Field(None, gt=0)
    original_usable_capacity_kwh: Optional[float] = Field(None, gt=0)
    current_soc: Optional[float] = Field(None, ge=0.0, le=100.0)
    notes: Optional[str] = None


class VehicleProfileResponse(VehicleProfileBase):
    id: int
    created_at: str
    updated_at: str


# --- Charging Reading Schemas ---

class ChargingReadingItem(BaseModel):
    elapsed_minutes: float = Field(..., ge=0.0, description="Elapsed time in minutes")
    timestamp: Optional[str] = None
    soc_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="SoC percentage (None if missing)")
    power_kw: Optional[float] = Field(None, ge=0.0, description="Charging power in kW")
    cumulative_energy_kwh: Optional[float] = Field(None, ge=0.0, description="Cumulative meter energy in kWh")
    is_estimated: Optional[bool] = False
    notes: Optional[str] = None


class ChargingSessionCreate(BaseModel):
    vehicle_profile_id: Optional[int] = None
    session_name: str = Field(..., min_length=1)
    start_time: Optional[str] = None
    data_source: str = Field(default="manual", description="manual, csv, or simulation")
    notes: Optional[str] = None
    readings: List[ChargingReadingItem] = Field(default_factory=list)


class ChargingSessionResponse(BaseModel):
    id: int
    vehicle_profile_id: Optional[int]
    session_name: str
    start_time: Optional[str]
    data_source: str
    notes: Optional[str]
    created_at: str
    readings: List[Dict[str, Any]] = Field(default_factory=list)


# --- Numerical Analysis Request/Response Schemas ---

class InterpolateRequest(BaseModel):
    readings: List[ChargingReadingItem]
    method: str = Field(default="linear", description="'linear' or 'newton'")
    max_gap_minutes: float = Field(default=30.0, gt=0)


class EnergyCalculationRequest(BaseModel):
    t_minutes: List[float] = Field(..., min_length=2)
    power_kw: List[float] = Field(..., min_length=2)
    method: str = Field(default="trapezoidal", description="'trapezoidal' or 'simpson'")


class ChargingTimeEstimateRequest(BaseModel):
    usable_capacity_kwh: float = Field(..., gt=0)
    current_soc: float = Field(..., ge=0.0, le=100.0)
    target_soc: float = Field(..., ge=0.0, le=100.0)
    constant_power_kw: Optional[float] = Field(None, gt=0)
    observed_soc_power_pairs: Optional[List[List[float]]] = None  # [[soc, kw], ...]


class RangePredictRequest(BaseModel):
    usable_capacity_kwh: float = Field(..., gt=0)
    current_soc_percent: float = Field(..., ge=0.0, le=100.0)
    consumption_kwh_per_km: Optional[float] = Field(None, gt=0)
    use_trips_regression: bool = Field(default=False)
    trip_distances_km: Optional[List[float]] = None
    trip_energies_kwh: Optional[List[float]] = None


class TripFeasibilityRequest(BaseModel):
    usable_capacity_kwh: float = Field(..., gt=0)
    starting_soc_percent: float = Field(..., ge=0.0, le=100.0)
    journey_distance_km: float = Field(..., gt=0)
    consumption_rate_kwh_per_km: float = Field(..., gt=0)
    desired_reserve_percent: float = Field(default=10.0, ge=0.0, le=50.0)


class BatteryHealthRequest(BaseModel):
    original_usable_capacity_kwh: float = Field(..., gt=0)
    current_usable_capacity_kwh: float = Field(..., gt=0)
    historical_measurements: Optional[List[Dict[str, Any]]] = None  # [{"date": "...", "capacity_kwh": ...}]


class MethodComparisonRequest(BaseModel):
    category: str = Field(..., description="'integration', 'interpolation', or 'root_finding'")
    dataset: Dict[str, Any]


class AnalysisRecordCreate(BaseModel):
    vehicle_profile_id: Optional[int] = None
    analysis_type: str
    title: str
    input_snapshot: Dict[str, Any]
    result_snapshot: Dict[str, Any]
    method_used: str


class AnalysisRecordResponse(BaseModel):
    id: int
    vehicle_profile_id: Optional[int]
    analysis_type: str
    title: Optional[str]
    input_snapshot: Dict[str, Any]
    result_snapshot: Dict[str, Any]
    method_used: str
    created_at: str
