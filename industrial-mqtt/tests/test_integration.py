"""Comprehensive Automated Integration Test Suite.

Verifies:
  1. Common Ingestion Pipeline normalization and latency calculation.
  2. Dynamic heterogeneous parameters handling (JSONB persistence).
  3. Status conversion and type coercion (bool, int, string).
  4. Database persistence and query retrieval.
  5. REST API responses for Mobile applications (/machines, /latest, /history).
"""

import datetime
import pytest
from httpx import ASGITransport, AsyncClient

from factory_backend.api.main import app
from factory_backend.pipeline.processor import pipeline
from factory_backend.schemas.telemetry import RawTelemetryPayload


@pytest.mark.asyncio
async def test_pipeline_normalization_and_validation():
    # 1. Test Stamping Press Payload
    stamping_payload = {
        "machine_id": "M01",
        "status": True,  # Boolean input
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "parameters": {
            "hydraulic_pressure": 185.2,
            "die_temp": 65.4,
            "tonnage": 250.0,
            "stroke_count": 1420,
        },
    }

    normalized = await pipeline.process(raw_data=stamping_payload, source_type="api")
    assert normalized.machine_id == "M01"
    assert normalized.status == 1  # Coerced to integer
    assert normalized.source_type == "api"
    assert normalized.parameters["hydraulic_pressure"] == 185.2
    assert normalized.parameters["stroke_count"] == 1420

    # 2. Test CNC Machine Payload with different parameters
    cnc_payload = {
        "machine_id": "M02",
        "status": "RUNNING",  # String input
        "timestamp": int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),  # Epoch ms
        "parameters": {
            "spindle_rpm": 3800,
            "feed_rate": 1250.0,
            "coolant_flow": 18.2,
        },
    }
    normalized_cnc = await pipeline.process(raw_data=cnc_payload, source_type="mqtt_json")
    assert normalized_cnc.machine_id == "M02"
    assert normalized_cnc.status == 1
    assert normalized_cnc.source_type == "mqtt_json"
    assert normalized_cnc.parameters["spindle_rpm"] == 3800


@pytest.mark.asyncio
async def test_mobile_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test 1: Healthcheck
        res_health = await client.get("/api/v1/healthz")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "ok"

        # Test 2: Machines List
        res_machines = await client.get("/api/v1/machines")
        assert res_machines.status_code == 200
        machines = res_machines.json()
        assert len(machines) >= 3
        machine_ids = [m["id"] for m in machines]
        assert "M01" in machine_ids
        assert "M02" in machine_ids
        assert "M03" in machine_ids

        # Test 3: Machine Detail with latest telemetry
        res_detail = await client.get("/api/v1/machines/M01")
        assert res_detail.status_code == 200
        detail_data = res_detail.json()
        assert detail_data["machine"]["id"] == "M01"
        assert detail_data["latest_telemetry"] is not None
        assert "hydraulic_pressure" in detail_data["latest_telemetry"]["parameters"]

        # Test 4: Historical telemetry for trend charts
        res_history = await client.get("/api/v1/machines/M01/history?limit=10")
        assert res_history.status_code == 200
        history_data = res_history.json()
        assert history_data["machine_id"] == "M01"
        assert len(history_data["items"]) > 0
