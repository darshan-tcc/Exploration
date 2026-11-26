"""Database models for machines, telemetry (with JSONB), and shift summaries."""

import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from factory_backend.db.session import Base


class Machine(Base):
    """Machine master definition."""

    __tablename__ = "machines"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # e.g. "M01", "Machine01_Stamping"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False, default="Plant1")
    line_id: Mapped[str] = mapped_column(String(50), nullable=False, default="Line1")
    machine_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "stamping", "cnc", "packaging"
    plc_model: Mapped[str] = mapped_column(String(50), nullable=True, default="Siemens S7-1500")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 1=Running, 0=Stopped/Alarm
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    telemetry_records: Mapped[list["MachineTelemetry"]] = relationship(
        "MachineTelemetry", back_populates="machine", cascade="all, delete-orphan"
    )
    shift_summaries: Mapped[list["MachineShiftSummary"]] = relationship(
        "MachineShiftSummary", back_populates="machine", cascade="all, delete-orphan"
    )


class MachineTelemetry(Base):
    """High-frequency machine telemetry table.
    
    Uses JSONB for 'parameters' to dynamically support distinct metrics across 
    different machine types (Stamping tonnage, CNC RPM/feed, Packaging speed).
    """

    __tablename__ = "machine_telemetry"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(String(50), ForeignKey("machines.id"), nullable=False, index=True)
    
    # Ingestion Source & Status
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "api", "mqtt_json", "sparkplug_b"
    status: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=Running, 0=Stopped

    # Dynamic metrics payload stored in JSONB
    # e.g.: {"hydraulic_pressure": 182.4, "die_temp": 64.2, "stroke_count": 1450}
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    received_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    machine: Mapped["Machine"] = relationship("Machine", back_populates="telemetry_records")

    __table_args__ = (
        # Optimized composite index for fetching the latest telemetry for a machine
        Index("idx_telemetry_machine_timestamp", "machine_id", "timestamp"),
        # GIN index for JSONB parameter lookups
        Index("idx_telemetry_parameters_gin", "parameters", postgresql_using="gin"),
    )


class MachineShiftSummary(Base):
    """Matches the user's MES Shift & OEE summary specification."""

    __tablename__ = "machine_shift_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(String(50), ForeignKey("machines.id"), nullable=False, index=True)
    machine_name: Mapped[str] = mapped_column(String(100), nullable=False)
    line_id: Mapped[str] = mapped_column(String(50), nullable=False)
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False)

    production_count_day: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_quantity_day: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    oee_scrap_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    oee_prod_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    operator_name: Mapped[str] = mapped_column(String(100), nullable=False, default="Operator 1")
    machine_status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    performance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    availability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    oee: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    shift_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    shift_start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    shift_end_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    shift_date: Mapped[datetime.date] = mapped_column(nullable=False)

    runtime_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    downtime_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    idle_time_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    machine: Mapped["Machine"] = relationship("Machine", back_populates="shift_summaries")
