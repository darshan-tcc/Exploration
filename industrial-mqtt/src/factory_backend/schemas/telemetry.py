"""Pydantic schemas for data validation, normalization, and API transport."""

import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator


class RawTelemetryPayload(BaseModel):
    """Schema for incoming raw telemetry (from either HTTP API or MQTT JSON)."""

    machine_id: str = Field(..., description="Unique machine identifier (e.g. M01, Machine01_Stamping)")
    status: int | bool = Field(..., description="1/True = Running, 0/False = Stopped/Alarm")
    timestamp: datetime.datetime | int | float | str | None = Field(
        default=None, description="Event timestamp from machine/edge"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Dynamic, machine-specific sensor readings"
    )

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v: Any) -> int:
        """Coerce boolean or integer status to 0 or 1."""
        if isinstance(v, bool):
            return 1 if v else 0
        if isinstance(v, int | float):
            return 1 if int(v) > 0 else 0
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower in ("running", "1", "true", "on", "ok"):
                return 1
            return 0
        return 0


class NormalizedTelemetry(BaseModel):
    """Common internal representation output by the Ingestion Pipeline."""

    machine_id: str
    status: int
    source_type: str  # "api", "mqtt_json", "sparkplug_b"
    timestamp: datetime.datetime
    received_at: datetime.datetime
    parameters: dict[str, Any]
    ingestion_latency_ms: float = 0.0


class MachineResponse(BaseModel):
    """Machine detail response model."""

    id: str
    name: str
    plant_id: str
    line_id: str
    machine_type: str
    plc_model: str | None
    status: int
    is_active: bool
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class LatestMachineState(BaseModel):
    """Composite snapshot for mobile cards."""

    machine: MachineResponse
    latest_telemetry: NormalizedTelemetry | None
