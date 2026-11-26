"""Mobile & Consumer API Endpoints.

Provides:
  - GET /api/v1/machines (List machines, types, current status)
  - GET /api/v1/machines/{id} (Machine detail + latest dynamic telemetry)
  - GET /api/v1/machines/{id}/history (Historical telemetry with pagination)
  - GET /api/v1/healthz & /readyz (Operational health check)
  - WS  /api/v1/ws/live (Real-time WebSocket telemetry push)
"""

import asyncio
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from factory_backend.db.models import Machine, MachineTelemetry
from factory_backend.db.session import get_db_session
from factory_backend.pipeline.processor import pipeline
from factory_backend.schemas.telemetry import LatestMachineState, MachineResponse, NormalizedTelemetry

router = APIRouter(prefix="/api/v1", tags=["Mobile & Factory APIs"])


@router.get("/healthz")
async def health_check():
    """Liveness probe."""
    return {"status": "ok", "service": "factory_backend"}


@router.get("/readyz")
async def readiness_check(session: AsyncSession = Depends(get_db_session)):
    """Readiness probe checking database connectivity."""
    try:
        await session.execute(select(1))
        return {"status": "ready", "database": "connected"}
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unready: {str(ex)}",
        )


@router.get("/machines", response_model=list[MachineResponse])
async def list_machines(session: AsyncSession = Depends(get_db_session)):
    """Lists all configured machines across plants and lines."""
    result = await session.execute(select(Machine).order_by(Machine.id))
    return result.scalars().all()


@router.get("/machines/{machine_id}", response_model=LatestMachineState)
async def get_machine_detail(machine_id: str, session: AsyncSession = Depends(get_db_session)):
    """Fetches a machine's metadata alongside its current live telemetry snapshot."""
    machine = await session.get(Machine, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

    # Fast hot cache lookup first
    cached_telemetry = pipeline.get_latest_cached(machine_id)

    # Fallback to DB if cache is cold
    if not cached_telemetry:
        result = await session.execute(
            select(MachineTelemetry)
            .where(MachineTelemetry.machine_id == machine_id)
            .order_by(desc(MachineTelemetry.timestamp))
            .limit(1)
        )
        record = result.scalars().first()
        if record:
            cached_telemetry = NormalizedTelemetry(
                machine_id=record.machine_id,
                status=record.status,
                source_type=record.source_type,
                timestamp=record.timestamp,
                received_at=record.received_at,
                parameters=record.parameters,
                ingestion_latency_ms=0.0,
            )

    return LatestMachineState(
        machine=MachineResponse.model_validate(machine),
        latest_telemetry=cached_telemetry,
    )


@router.get("/machines/{machine_id}/history")
async def get_machine_history(
    machine_id: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
):
    """Returns paginated time-series telemetry for trending charts in mobile apps."""
    result = await session.execute(
        select(MachineTelemetry)
        .where(MachineTelemetry.machine_id == machine_id)
        .order_by(desc(MachineTelemetry.timestamp))
        .offset(offset)
        .limit(limit)
    )
    records = result.scalars().all()
    return {
        "machine_id": machine_id,
        "count": len(records),
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": r.id,
                "status": r.status,
                "source_type": r.source_type,
                "parameters": r.parameters,
                "timestamp": r.timestamp.isoformat(),
                "received_at": r.received_at.isoformat(),
            }
            for r in records
        ],
    }


# ==============================================================================
# WebSocket Real-Time Telemetry Stream for Mobile & Dashboards
# ==============================================================================
@router.websocket("/ws/live")
async def live_telemetry_ws(websocket: WebSocket, machine_id: str | None = None):
    """High-performance WebSocket connection pushing live telemetry updates.
    
    Optional query parameter:
      ?machine_id=M01 (Filters updates to a specific machine only)
    """
    await websocket.accept()

    # Callback registered to the pipeline
    async def on_telemetry(telemetry: NormalizedTelemetry):
        if machine_id and telemetry.machine_id != machine_id:
            return
        await websocket.send_json({
            "event": "telemetry_update",
            "data": telemetry.model_dump(mode="json"),
        })

    pipeline.register_listener(on_telemetry)
    try:
        # Keep connection open and listen for client pings or filters
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pipeline.unregister_listener(on_telemetry)
    except Exception:
        pipeline.unregister_listener(on_telemetry)
