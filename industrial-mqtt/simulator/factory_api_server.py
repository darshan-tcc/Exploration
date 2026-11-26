"""Simulated Factory API Server.

Exposes REST endpoints that mimic an existing factory MES/SCADA system:
  - GET /api/v1/factory/machines/telemetry (Requires X-API-KEY header)
  - GET /api/v1/factory/shifts/summary
"""

import datetime
import random
from fastapi import FastAPI, Header, HTTPException, status
import uvicorn

app = FastAPI(title="Simulated Factory MES API", version="1.0.0")

EXPECTED_API_KEY = "plant-secret-api-token-2026"

# Internal state of simulated factory machines
FACTORY_STATE = {
    "M01": {
        "machine_id": "M01",
        "name": "Machine01_Stamping",
        "status": 1,
        "hydraulic_pressure": 182.5,
        "die_temp": 64.0,
        "tonnage": 248.0,
        "stroke_count": 1450,
        "lubrication_level": 85.5,
    },
    "M02": {
        "machine_id": "M02",
        "name": "Machine02_CNC",
        "status": 1,
        "spindle_rpm": 3800,
        "feed_rate": 1250.0,
        "tool_wear": 15.2,
        "coolant_flow": 18.5,
    },
    "M03": {
        "machine_id": "M03",
        "name": "Machine03_Packaging",
        "status": 1,
        "conveyor_speed": 1.30,
        "carton_count": 920,
        "sealing_temp": 146.0,
        "jam_alarm": False,
    },
}


def verify_api_key(x_api_key: str | None = Header(None)):
    if x_api_key != EXPECTED_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-KEY header",
        )


@app.get("/api/v1/factory/machines/telemetry", dependencies=[verify_api_key])
async def get_machines_telemetry():
    """Returns telemetry snapshot for all factory machines with dynamic physics."""
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    telemetry_list = []

    # 1. Update M01
    s1 = FACTORY_STATE["M01"]
    s1["status"] = 1 if random.random() > 0.10 else 0
    if s1["status"] == 1:
        s1["stroke_count"] += random.randint(1, 3)
        s1["hydraulic_pressure"] = round(random.uniform(178.0, 192.0), 1)
        s1["die_temp"] = round(min(90.0, s1["die_temp"] + random.uniform(-0.3, 0.5)), 1)
        s1["tonnage"] = round(random.uniform(235.0, 252.0), 1)
    telemetry_list.append({
        "machine_id": s1["machine_id"],
        "status": s1["status"],
        "timestamp": now_utc,
        "parameters": {
            "hydraulic_pressure": s1["hydraulic_pressure"],
            "die_temp": s1["die_temp"],
            "tonnage": s1["tonnage"],
            "stroke_count": s1["stroke_count"],
            "lubrication_level": s1["lubrication_level"],
        },
    })

    # 2. Update M02
    s2 = FACTORY_STATE["M02"]
    s2["status"] = 1 if random.random() > 0.10 else 0
    if s2["status"] == 1:
        s2["spindle_rpm"] = random.randint(3500, 4100)
        s2["feed_rate"] = round(random.uniform(1200.0, 1300.0), 1)
        s2["tool_wear"] = round(s2["tool_wear"] + 0.01, 2)
        s2["coolant_flow"] = round(random.uniform(17.0, 19.5), 1)
    else:
        s2["spindle_rpm"] = 0
    telemetry_list.append({
        "machine_id": s2["machine_id"],
        "status": s2["status"],
        "timestamp": now_utc,
        "parameters": {
            "spindle_rpm": s2["spindle_rpm"],
            "feed_rate": s2["feed_rate"],
            "tool_wear": s2["tool_wear"],
            "coolant_flow": s2["coolant_flow"],
        },
    })

    # 3. Update M03
    s3 = FACTORY_STATE["M03"]
    jam = random.random() < 0.05
    s3["jam_alarm"] = jam
    s3["status"] = 0 if jam else (1 if random.random() > 0.08 else 0)
    if s3["status"] == 1:
        s3["carton_count"] += random.randint(1, 4)
        s3["conveyor_speed"] = round(random.uniform(1.20, 1.38), 2)
        s3["sealing_temp"] = round(random.uniform(144.0, 148.0), 1)
    else:
        s3["conveyor_speed"] = 0.0
    telemetry_list.append({
        "machine_id": s3["machine_id"],
        "status": s3["status"],
        "timestamp": now_utc,
        "parameters": {
            "conveyor_speed": s3["conveyor_speed"],
            "carton_count": s3["carton_count"],
            "sealing_temp": s3["sealing_temp"],
            "jam_alarm": s3["jam_alarm"],
        },
    })

    return {
        "status": "success",
        "plant_id": "Plant1",
        "line_id": "Line1",
        "timestamp": now_utc,
        "data": telemetry_list,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8005, log_level="warning")
