"""Common Data Ingestion Pipeline: Normalization, validation, persistence & live push."""

import datetime
from typing import Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from factory_backend.db.models import Machine, MachineTelemetry
from factory_backend.db.session import async_session_factory
from factory_backend.schemas.telemetry import NormalizedTelemetry, RawTelemetryPayload


class TelemetryPipeline:
    """Central processing pipeline feeding from both Factory API and MQTT."""

    def __init__(self):
        # In-memory fast cache for instant mobile app queries
        self._latest_cache: dict[str, NormalizedTelemetry] = {}
        # Subscribers for live WebSocket streaming
        self._listeners: set[Any] = set()

    def register_listener(self, listener):
        self._listeners.add(listener)

    def unregister_listener(self, listener):
        self._listeners.discard(listener)

    def get_latest_cached(self, machine_id: str) -> NormalizedTelemetry | None:
        return self._latest_cache.get(machine_id)

    def get_all_latest_cached(self) -> dict[str, NormalizedTelemetry]:
        return self._latest_cache.copy()

    def normalize(self, raw: RawTelemetryPayload, source_type: str) -> NormalizedTelemetry:
        """Standardizes timestamps, sanitizes parameter names, calculates latency."""
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        # Parse or default the event timestamp
        event_time: datetime.datetime
        if raw.timestamp is None:
            event_time = now_utc
        elif isinstance(raw.timestamp, int | float):
            # Epoch milliseconds or seconds
            if raw.timestamp > 1e11:  # milliseconds
                event_time = datetime.datetime.fromtimestamp(raw.timestamp / 1000.0, tz=datetime.timezone.utc)
            else:
                event_time = datetime.datetime.fromtimestamp(raw.timestamp, tz=datetime.timezone.utc)
        elif isinstance(raw.timestamp, str):
            try:
                event_time = datetime.datetime.fromisoformat(raw.timestamp)
                if event_time.tzinfo is None:
                    event_time = event_time.replace(tzinfo=datetime.timezone.utc)
            except Exception:
                event_time = now_utc
        else:
            event_time = raw.timestamp if raw.timestamp.tzinfo else raw.timestamp.replace(tzinfo=datetime.timezone.utc)

        # Calculate latency
        latency_ms = max(0.0, (now_utc - event_time).total_seconds() * 1000.0)

        # Sanitize parameter keys (lowercase, no extra spaces)
        cleaned_params: dict[str, Any] = {}
        for k, v in raw.parameters.items():
            clean_key = k.strip().replace(" ", "_")
            cleaned_params[clean_key] = v

        return NormalizedTelemetry(
            machine_id=raw.machine_id,
            status=raw.status,
            source_type=source_type,
            timestamp=event_time,
            received_at=now_utc,
            parameters=cleaned_params,
            ingestion_latency_ms=round(latency_ms, 2),
        )

    async def process(self, raw_data: dict[str, Any], source_type: str) -> NormalizedTelemetry:
        """Main pipeline entrypoint: Validate -> Normalize -> Persist -> Broadcast."""
        # 1. Validation with Pydantic
        raw_payload = RawTelemetryPayload(**raw_data)

        # 2. Normalization
        normalized = self.normalize(raw_payload, source_type=source_type)

        # 3. Update fast in-memory hot cache
        self._latest_cache[normalized.machine_id] = normalized

        # 4. Asynchronous Database Persistence (Non-blocking)
        async with async_session_factory() as session:
            async with session.begin():
                # Record telemetry log
                record = MachineTelemetry(
                    machine_id=normalized.machine_id,
                    source_type=normalized.source_type,
                    status=normalized.status,
                    parameters=normalized.parameters,
                    timestamp=normalized.timestamp,
                    received_at=normalized.received_at,
                )
                session.add(record)

                # Update current status on Machine master
                await session.execute(
                    update(Machine)
                    .where(Machine.id == normalized.machine_id)
                    .values(status=normalized.status, updated_at=normalized.received_at)
                )

        # 5. Broadcast to active WebSocket clients
        for listener in list(self._listeners):
            try:
                await listener(normalized)
            except Exception:
                pass

        return normalized


# Global singleton pipeline instance
pipeline = TelemetryPipeline()
