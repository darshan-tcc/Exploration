# Factory Data Integration & Industrial MQTT — Master Implementation Plan & Architecture Blueprint

> **Goal:** Build a production-grade, local, modular backend system simulating how a modern manufacturing facility exposes machine data to external mobile and SCADA applications. The system supports dual ingestion: **Factory API Polling (Architecture A)** and **Industrial MQTT / Sparkplug B streaming (Architecture B)**, passes all data through a unified validation and normaliza# Factory Data Integration Backend — Master Roadmap & Blueprint

> **Goal:** Build a production-grade, local, modular backend system simulating a real manufacturing facility. The backend natively supports both **Factory API Polling (Architecture A)** and **Industrial MQTT / Sparkplug B streaming (Architecture B)**, ingests into a common normalization pipeline, persists into PostgreSQL with JSONB dynamic telemetry, and serves clean REST & WebSocket APIs for mobile applications (Flutter / React Native).

---

## 1. System Architecture Diagram

```mermaid
flowchart TD
    subgraph Sources["Industrial Sources & Simulation"]
        API_Sim["Simulated Factory API Server<br/>(HTTP JSON, Auth, Shifts)"]
        MQTT_Sim["Simulated Machines<br/>(Paho / Sparkplug B / JSON)"]
    end

    subgraph Infra["Infrastructure (Docker Compose)"]
        Mosquitto["Mosquitto MQTT Broker<br/>(ACLs, Auth, Ports 1883/8883)"]
        Postgres[("PostgreSQL 16 DB<br/>(SQLAlchemy + Alembic + JSONB)")]
    end

    subgraph BackendApp["Modular Backend System (FastAPI + Asyncio)"]
        subgraph Ingestion["Ingestion Adapters"]
            HttpPoller["Architecture A: API Poller<br/>(HTTPX Async Worker)"]
            MqttSub["Architecture B: MQTT Subscriber<br/>(Paho Async Worker)"]
        end

        subgraph Pipeline["Common Ingestion Pipeline"]
            Validator["Pydantic v2 Validator<br/>(Strict & Dynamic Schemas)"]
            Normalizer["Telemetry Normalizer & Unit Converter"]
            Enricher["Ingestion Metadata & Time Align"]
        end

        subgraph ServiceLayer["Service & Repository Layer"]
            MachineService["Machine Service & Shift Engine"]
            TelemetryRepo["Telemetry Repository<br/>(Batching, Latest State, History)"]
        end

        subgraph API["Mobile & Consumer Endpoints"]
            FastAPI_REST["FastAPI REST Endpoints<br/>(Machines, Telemetry, OEE, History)"]
            FastAPI_WS["WebSocket Live Stream<br/>(Push on Telemetry Update)"]
        end
    end

    subgraph Clients["Consumers"]
        MobileApp["Mobile App (Flutter / React Native)"]
        Ignition["Ignition SCADA / External Systems"]
    end

    API_Sim -->|HTTP GET/POST Polling| HttpPoller
    MQTT_Sim -->|Publish Telemetry| Mosquitto
    Mosquitto -->|Subscribe Topics| MqttSub
    Mosquitto -->|Sparkplug B Auto-Discovery| Ignition

    HttpPoller --> Pipeline
    MqttSub --> Pipeline
    Validator --> Normalizer --> Enricher --> MachineService
    MachineService --> TelemetryRepo --> Postgres

    TelemetryRepo --> FastAPI_REST
    MachineService -->|Live Broadcast| FastAPI_WS
    FastAPI_REST --> MobileApp
    FastAPI_WS --> MobileApp
```

---

## 2. Directory & Modular Code Structure

We will organize the repository using a clean, scalable hexagonal/clean architecture:

```text
industrial-mqtt/
├── docker/
│   ├── docker-compose.yml           # Postgres, Mosquitto, Adminer
│   ├── mosquitto/
│   │   ├── config/mosquitto.conf    # Auth & ACL configuration
│   │   ├── config/password_file     # Encrypted broker credentials
│   │   └── config/acl_file          # Topic-level read/write permissions
│   └── postgres/
│       └── init.sql                 # Initial schema & extensions
├── src/
│   └── factory_backend/
│       ├── __init__.py
│       ├── core/                    # App config, security, logging
│       │   ├── config.py            # Pydantic Settings & .env loading
│       │   ├── logging.py           # Structured JSON/Console logging
│       │   └── security.py          # API Auth, JWT, Hashing
│       ├── db/                      # Database models, session & migrations
│       │   ├── session.py           # Async SQLAlchemy engine & sessionmaker
│       │   ├── base.py              # Declarative Base
│       │   ├── models/
│       │   │   ├── machine.py       # Machine master, lines, plants
│       │   │   ├── telemetry.py     # High-frequency readings (with JSONB)
│       │   │   └── shift_summary.py # OEE & shift production records
│       │   └── migrations/          # Alembic migrations folder
│       ├── schemas/                 # Pydantic validation & transfer objects
│       │   ├── telemetry.py         # Ingestion payload & normalized schemas
│       │   ├── machine.py           # Machine response models
│       │   └── common.py            # Unified response wrappers & pagination
│       ├── pipeline/                # Common Ingestion Engine
│       │   ├── normalizer.py        # Maps raw telemetry to normalized model
│       │   ├── validator.py         # Type coercion & rule checks
│       │   └── processor.py         # Pipeline coordinator (feeds DB & WS)
│       ├── integrations/            # Ingestion Adapters
│       │   ├── base.py              # IngestionAdapter interface
│       │   ├── api_poller.py        # Architecture A: Factory HTTP API Poller
│       │   └── mqtt_listener.py     # Architecture B: MQTT/Sparkplug Subscriber
│       ├── services/                # Business logic
│       │   ├── machine_service.py   # State tracking & OEE calculation
│       │   └── telemetry_service.py # Telemetry query & history aggregation
│       └── api/                     # Mobile-facing FastAPI presentation layer
│           ├── deps.py              # DB & Auth dependencies
│           ├── v1/
│           │   ├── router.py        # Main v1 router
│           │   ├── machines.py      # /api/v1/machines (list, detail, status)
│           │   ├── telemetry.py     # /api/v1/telemetry (latest, history)
│           │   ├── health.py        # /healthz, /readyz endpoints
│           │   └── ws.py            # /ws/live (WebSocket real-time push)
│           └── main.py              # FastAPI application bootstrap
├── simulator/
│   ├── factory_api_server.py        # Simulates factory HTTP JSON API
│   ├── mqtt_publisher.py            # Simulates multi-machine MQTT payloads
│   └── sparkplug_factory.py         # Protobuf Sparkplug B publisher
├── tests/
│   ├── test_pipeline.py             # Validation & normalization tests
│   ├── test_integrations.py         # API Poller & MQTT Subscriber tests
│   └── test_api.py                  # FastAPI endpoint integration tests
├── .env.example                     # Reference environment variables
├── pyproject.toml                   # Project dependencies
└── README.md
```

---

## 3. Step-by-Step Implementation Phases

### **Phase 1: Environment, Dependencies & Docker Infrastructure**
- [ ] Add necessary packages: `fastapi`, `uvicorn`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic-settings`, `httpx`, `paho-mqtt`, `pytest`.
- [ ] Create `.env.example` and `.env` for secrets and credentials.
- [ ] Set up `docker-compose.yml` with:
  - **PostgreSQL 16**: Port 5432 with healthchecks and persistent volume.
  - **Mosquitto 2.0**: Configured with username/password authentication & ACLs.
- [ ] Verify Docker containers launch cleanly and are reachable.

### **Phase 2: Database Layer (SQLAlchemy 2.0 + Alembic + JSONB)**
- [ ] Configure async database session in `src/factory_backend/db/session.py`.
- [ ] Create models:
  - `Machine`: Static configuration (ID, name, plant, line, model, status).
  - `MachineTelemetry`: Unified record with `timestamp`, `received_at`, `status`, and **`parameters (JSONB)`** to support heterogeneous, dynamic machine metrics.
  - `MachineShiftSummary`: Matches the user's MES OEE table.
- [ ] Initialize Alembic and generate the initial migration.

### **Phase 3: Common Data Pipeline & Normalization**
- [ ] Define Pydantic models for incoming raw data and normalized internal representations.
- [ ] Implement `normalizer.py`:
  - Standardizes timestamps (ISO 8601 UTC).
  - Normalizes machine IDs and metric names.
  - Adds backend ingestion metadata (`source_type`: `"api"` or `"mqtt"`, `ingested_at`, `latency_ms`).
- [ ] Implement `processor.py`: Decouples the data ingestion source from database storage and WebSocket broadcasting.

### **Phase 4: Ingestion Integrations (Architecture A & B)**
- [ ] **Architecture A (Factory API Poller)**:
  - Create `simulator/factory_api_server.py` exposing mock factory endpoints with API-key authentication.
  - Implement `integrations/api_poller.py` using `httpx` async background worker to poll and feed the pipeline.
- [ ] **Architecture B (MQTT Integration)**:
  - Configure Mosquitto user accounts and ACLs.
  - Implement `integrations/mqtt_listener.py` supporting both standard JSON topics and Sparkplug B.
  - Feed MQTT events into the same common pipeline.

### **Phase 5: FastAPI Mobile-Facing Layer & Real-Time Push**
- [ ] Build `/api/v1/machines` (overview, status, active alarms).
- [ ] Build `/api/v1/telemetry/latest` and `/api/v1/telemetry/history` with pagination and date range filters.
- [ ] Build `/ws/live` WebSocket endpoint for real-time telemetry streaming to mobile clients.
- [ ] Provide operational health endpoints (`/healthz`, `/readyz`).

### **Phase 6: Verification, Testing & Failure Scenarios**
- [ ] Run end-to-end integration test with both sources streaming simultaneously.
- [ ] Test edge cases: missing parameters, network disconnection, duplicate packets, invalid JSON payloads.
- [ ] Verify query performance on PostgreSQL using JSONB indexes.
tion pipeline, persists heterogeneous parameters in PostgreSQL via **JSONB**, and serves mobile applications (Flutter / React Native) through clean REST and real-time WebSocket endpoints.

---

## 1. Project Overview & Requirements Matrix (All 12 Scopes)

| # | Requirement Scope | Implementation in this System | Key Technologies / Files |
|---|---|---|---|
| **1** | **Local Environment & Infra** | Modular Python backend (`src/factory_backend/`), PostgreSQL database, environment configuration (`.env`). | `pyproject.toml`, `requirements.txt`, `.env` |
| **2** | **Architecture A: Factory API** | Simulated factory MES REST API on port 8005 with `X-API-KEY` auth; async polling worker. | `simulator/factory_api_server.py`, `src/factory_backend/integrations/api_poller.py` |
| **3** | **Architecture B: MQTT Integration** | Industrial MQTT with wildcard topic subscription (`plant/+/+/telemetry`), Sparkplug B compatibility. | `simulator/sparkplug_factory.py`, `simulator/mqtt_publisher.py`, `src/factory_backend/integrations/mqtt_listener.py` |
| **4** | **Dynamic Telemetry Simulation** | Multi-machine simulation with distinct parameters (Stamping, CNC, Packaging) and dynamic state transitions (Running, Idle, Alarm). | `simulator/sparkplug_factory.py`, `simulator/mqtt_publisher.py` |
| **5** | **Authentication & Security** | `X-API-KEY` header authentication, MQTT client credentials, environment variable isolation, credentials protected from Git. | `.env`, `.env.example`, `src/factory_backend/core/config.py` |
| **6** | **Data Formats & Protobuf** | UTF-8 JSON serialization/deserialization, Eclipse Sparkplug B binary Protocol Buffers encoding/decoding. | `pysparkplug`, `paho-mqtt`, `src/factory_backend/schemas/telemetry.py` |
| **7** | **Data Validation & Normalization** | Strict Pydantic v2 schemas, type coercion (booleans/integers/strings to binary status), ISO 8601 UTC timestamp alignment, latency calculation. | `src/factory_backend/schemas/telemetry.py`, `src/factory_backend/pipeline/processor.py` |
| **8** | **Database Design & Storage** | PostgreSQL tables (`Machine`, `MachineTelemetry`, `MachineShiftSummary`) with **JSONB** column for variable machine parameters. | `src/factory_backend/db/models.py`, `src/factory_backend/db/session.py` |
| **9** | **Common Ingestion Pipeline** | Unified pipeline feeding from both API poller and MQTT subscriber; decouples transport from storage and client push. | `src/factory_backend/pipeline/processor.py` |
| **10** | **FastAPI & Mobile APIs** | High-performance REST endpoints (`/machines`, `/history`, `/healthz`, `/readyz`) and real-time WebSocket (`/ws/live`). | `src/factory_backend/api/router.py`, `src/factory_backend/api/main.py` |
| **11** | **Testing & Failure Handling** | Automated pytest suite testing pipeline normalization, missing parameters, and REST endpoints. | `tests/test_integration.py` |
| **12** | **Logging & Operational Setup** | Structured async logging, operational health probes, graceful startup/teardown lifespan. | `src/factory_backend/api/main.py` |

---

## 2. Complete Target Architecture Diagram

```mermaid
flowchart TD
    subgraph Sources["1. Factory Sources & Simulators"]
        API_Sim["Factory HTTP API Server<br/>(simulator/factory_api_server.py)<br/>Port: 8005 | X-API-KEY Protected"]
        MQTT_Sim["Multi-Machine MQTT Simulators<br/>(sparkplug_factory.py / mqtt_publisher.py)<br/>Stamping, CNC, Packaging"]
    end

    subgraph Broker["2. Industrial MQTT Broker"]
        BrokerNode["Industrial MQTT Broker<br/>(Ignition MQTT Distributor / Mosquitto)<br/>Port: 1883"]
    end

    subgraph BackendApp["3. Factory Backend Service (FastAPI + Asyncio)"]
        subgraph Ingestion["Ingestion Adapters"]
            HttpPoller["Architecture A: API Poller<br/>(HTTPX Async Worker)"]
            MqttSub["Architecture B: MQTT Subscriber<br/>(Paho Async Worker)"]
        end

        subgraph Pipeline["Common Ingestion Pipeline"]
            Validator["Pydantic v2 Validator<br/>(Strict & Dynamic Schemas)"]
            Normalizer["Telemetry Normalizer & Unit Converter<br/>(ISO UTC, Status Coercion)"]
            HotCache[("In-Memory Hot Cache<br/>(O(1) Instant State Lookup)")]
        end

        subgraph Storage["Database Layer"]
            PG[("PostgreSQL Database<br/>- machines<br/>- machine_telemetry (JSONB)<br/>- machine_shift_summaries")]
        end

        subgraph Presentation["Mobile-Facing API Layer"]
            REST_API["FastAPI REST Endpoints<br/>GET /api/v1/machines<br/>GET /api/v1/machines/{id}/history"]
            WS_Hub["WebSocket Live Stream Hub<br/>WS /api/v1/ws/live"]
        end
    end

    subgraph Consumers["4. External Consumers"]
        MobileApp["Mobile App (Flutter / React Native)<br/>- Live Dashboard<br/>- Machine Cards<br/>- Historical Trends"]
        IgnitionSCADA["Ignition SCADA / Designer<br/>(Perspective HMI, Live Gauges)"]
    end

    API_Sim -->|HTTP GET Polling :8005| HttpPoller
    MQTT_Sim -->|Publish Telemetry :1883| BrokerNode
    BrokerNode -->|Subscribe: plant/+/+/telemetry| MqttSub
    BrokerNode -->|Sparkplug B Auto-Discovery| IgnitionSCADA

    HttpPoller --> Validator
    MqttSub --> Validator
    Validator --> Normalizer
    Normalizer --> HotCache
    Normalizer -->|Async Batch Insert| PG
    Normalizer -->|Push Broadcast| WS_Hub

    HotCache --> REST_API
    PG --> REST_API
    REST_API -->|HTTP JSON| MobileApp
    WS_Hub -->|Real-Time Push| MobileApp
```

---

## 3. Directory & Modular Code Structure

```text
industrial-mqtt/
├── .env                                # Local environment secrets and connection strings
├── .env.example                        # Template environment file
├── requirements.txt                    # Pip dependencies list
├── pyproject.toml                      # Modern packaging configuration
├── pytest.ini                          # Test configuration
├── MASTER_FACTORY_INTEGRATION_PLAN.md  # Complete project specification and guide
├── simulator/
│   ├── sparkplug_factory.py            # Architecture B: Sparkplug B Protobuf multi-machine simulation
│   ├── mqtt_publisher.py               # Architecture B: Standard JSON multi-machine MQTT publisher
│   ├── factory_api_server.py           # Architecture A: Simulated Factory MES REST API (port 8005)
│   └── sample.json                     # Reference MES JSON payload structure
├── tests/
│   └── test_integration.py            # Automated integration test suite
└── src/
    └── factory_backend/
        ├── __init__.py
        ├── core/
        │   └── config.py               # Settings management via Pydantic Settings
        ├── db/
        │   ├── session.py              # Async SQLAlchemy session and PostgreSQL engine
        │   └── models.py               # Machine, MachineTelemetry (JSONB), MachineShiftSummary
        ├── schemas/
        │   └── telemetry.py            # Pydantic schemas, normalization rules, API response models
        ├── pipeline/
        │   └── processor.py            # Common Ingestion Pipeline, hot cache & WebSocket broadcasting
        ├── integrations/
        │   ├── api_poller.py           # Architecture A: Async Factory API Poller worker
        │   └── mqtt_listener.py        # Architecture B: Paho MQTT background subscriber
        └── api/
            ├── router.py               # FastAPI routes: /machines, /history, /healthz, /readyz, /ws/live
            └── main.py                 # Application lifespan, CORS, and entrypoint
```

---

## 4. Step-by-Step Implementation Roadmap

### **Phase 1: Environment & Local Services Setup**
1. **Python Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate       # On Linux
   # or .\.venv\Scripts\Activate.ps1 # On Windows
   pip install -r requirements.txt
   ```
2. **Environment Variables (`.env`)**:
   Configure database URL, API key, and MQTT broker host/port.

### **Phase 2: Database Layer with Dynamic JSONB Schema**
1. Configured in `src/factory_backend/db/session.py` and `models.py`.
2. Uses **`JSONB`** for the `parameters` column in `machine_telemetry`, allowing each machine type (Stamping Press, CNC, Packaging) to store its unique telemetry fields without requiring schema alterations.

### **Phase 3: Common Data Ingestion Pipeline**
1. Implemented in `src/factory_backend/pipeline/processor.py`.
2. Performs:
   - Status coercion (booleans, numbers, strings to `0` or `1`).
   - ISO 8601 UTC timestamp normalization.
   - Latency calculation in milliseconds (`received_at - event_timestamp`).
   - Non-blocking asynchronous persistence into PostgreSQL.
   - Hot cache update for instant $O(1)$ mobile query responses.
   - Broadcast to connected mobile WebSocket clients.

### **Phase 4: Dual Ingestion Integrations (Architecture A & B)**
1. **Architecture A (Factory API Poller)**:
   - `simulator/factory_api_server.py` simulates the factory MES API on port 8005.
   - `src/factory_backend/integrations/api_poller.py` polls the API using `httpx.AsyncClient` with `X-API-KEY`.
2. **Architecture B (Industrial MQTT)**:
   - `simulator/sparkplug_factory.py` publishes Sparkplug B Protobuf binary telemetry.
   - `simulator/mqtt_publisher.py` publishes JSON telemetry.
   - `src/factory_backend/integrations/mqtt_listener.py` subscribes to `plant/+/+/telemetry` and feeds into the common pipeline.

### **Phase 5: Mobile-Facing REST & WebSocket Layer**
1. `GET /api/v1/machines`: List all machines and operational statuses.
2. `GET /api/v1/machines/{id}`: Machine metadata + latest live telemetry snapshot.
3. `GET /api/v1/machines/{id}/history?limit=50`: Paginated time-series telemetry for trend charts.
4. `GET /api/v1/healthz` and `/api/v1/readyz`: Kubernetes-style operational probes.
5. `WS /api/v1/ws/live`: Real-time WebSocket feed pushing live updates with zero client polling.

### **Phase 6: Verification & Testing**
Run the automated test suite:
```bash
pytest tests/test_integration.py -v
```

---

## 5. Operations Quick Reference (Commands & URLs)

| Task | Command / Action |
|---|---|
| **Run Backend Server** | `python -m factory_backend.api.main` (or `uv run python -m factory_backend.api.main`) |
| **Run Factory API Simulator** | `python simulator/factory_api_server.py` |
| **Run Sparkplug B Simulator** | `python simulator/sparkplug_factory.py` |
| **Run JSON MQTT Simulator** | `python simulator/mqtt_publisher.py` |
| **Run Integration Tests** | `pytest tests/test_integration.py -v` |
| **Backend Interactive Docs** | Open browser to **`http://localhost:8000/docs`** |
| **Factory API Endpoint** | Open browser to **`http://localhost:8005/api/v1/factory/machines/telemetry`** |
| **Ignition Gateway Web** | Open browser to **`http://localhost:8088`** |

---

## 6. Complete Source Code by Module

### 6.1 `requirements.txt`
```text
paho-mqtt<2.0.0
pysparkplug>=0.3.0
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.9.0
pydantic-settings>=2.6.0
sqlalchemy[asyncio]>=2.0.36
asyncpg>=0.30.0
alembic>=1.14.0
httpx>=0.27.2
websockets>=13.1
python-dotenv>=1.0.1
pytest>=8.3.0
pytest-asyncio>=0.24.0
python-docx>=1.1.0
```

### 6.2 `pyproject.toml`
```toml
[project]
name = "industrial-mqtt"
version = "0.1.0"
description = "Industrial Factory Data Integration Backend"
readme = "README.md"
authors = [
    { name = "Darshan-T-P", email = "darshantp13@gmail.com" }
]
requires-python = ">=3.12"
dependencies = [
    "paho-mqtt<2.0.0",
    "pysparkplug>=0.3.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "httpx>=0.27.2",
    "websockets>=13.1",
    "python-dotenv>=1.0.1",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "python-docx>=1.2.0",
]

[project.scripts]
factory-backend = "factory_backend.api.main:start"

[build-system]
requires = ["uv_build>=0.12.7,<0.13.0"]
build-backend = "uv_build"
```

### 6.3 Environment Configuration (`.env.example`)
```ini
ENVIRONMENT=development
LOG_LEVEL=INFO
APP_HOST=0.0.0.0
APP_PORT=8000

# PostgreSQL Configuration
POSTGRES_USER=factory_user
POSTGRES_PASSWORD=factory_secure_pass_2026
POSTGRES_DB=factory_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://factory_user:factory_secure_pass_2026@localhost:5432/factory_db

# Architecture A: Factory API Integration
FACTORY_API_BASE_URL=http://localhost:8005/api/v1
FACTORY_API_KEY=plant-secret-api-token-2026
FACTORY_API_POLL_INTERVAL_SECONDS=3.0

# Architecture B: MQTT Broker Configuration
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=admin
MQTT_PASSWORD=changeme
MQTT_CLIENT_ID=factory_backend_subscriber
MQTT_TOPIC_TELEMETRY=plant/+/+/telemetry
MQTT_TOPIC_SPARKPLUG=spBv1.0/+/+/+
```

### 6.4 `simulator/sparkplug_factory.py` (Architecture B)
```python
"""Industrial Factory Line Simulation using Eclipse Sparkplug B."""

import random
import time
from pysparkplug import DataType, Device, EdgeNode, Metric, get_current_timestamp

GROUP_ID = "Plant1"
EDGE_NODE_ID = "Line1"
BROKER_HOST = "localhost"
BROKER_PORT = 1883

def m(name: str, datatype: DataType, value) -> Metric:
    return Metric(timestamp=get_current_timestamp(), name=name, datatype=datatype, value=value)

def create_stamping_press(device_id: str = "Machine01_Stamping"):
    state = {
        "status": 1,
        "hydraulic_pressure": 180.5,
        "die_temp": 62.0,
        "tonnage": 250.0,
        "stroke_count": 1420,
        "lubrication_level": 88.0,
    }
    metrics = [
        m("Status", DataType.INT32, state["status"]),
        m("Hydraulic_Pressure_Bar", DataType.FLOAT, state["hydraulic_pressure"]),
        m("Die_Temperature_C", DataType.FLOAT, state["die_temp"]),
        m("Tonnage_Actual_Tons", DataType.FLOAT, state["tonnage"]),
        m("Stroke_Count", DataType.INT64, state["stroke_count"]),
        m("Lubrication_Level_Pct", DataType.FLOAT, state["lubrication_level"]),
    ]
    return Device(device_id=device_id, metrics=metrics), state

def update_stamping_press(state: dict) -> list[Metric]:
    is_running = random.random() > 0.12
    state["status"] = 1 if is_running else 0
    if is_running:
        state["stroke_count"] += random.randint(1, 3)
        state["hydraulic_pressure"] = round(random.uniform(175.0, 195.0), 1)
        state["die_temp"] = round(min(95.0, state["die_temp"] + random.uniform(-0.4, 0.8)), 1)
        state["tonnage"] = round(random.uniform(230.0, 255.0), 1)
        state["lubrication_level"] = max(10.0, round(state["lubrication_level"] - 0.02, 2))
    else:
        state["hydraulic_pressure"] = round(random.uniform(30.0, 45.0), 1)
        state["die_temp"] = round(max(30.0, state["die_temp"] - 0.5), 1)
        state["tonnage"] = 0.0

    return [
        m("Status", DataType.INT32, state["status"]),
        m("Hydraulic_Pressure_Bar", DataType.FLOAT, state["hydraulic_pressure"]),
        m("Die_Temperature_C", DataType.FLOAT, state["die_temp"]),
        m("Tonnage_Actual_Tons", DataType.FLOAT, state["tonnage"]),
        m("Stroke_Count", DataType.INT64, state["stroke_count"]),
        m("Lubrication_Level_Pct", DataType.FLOAT, state["lubrication_level"]),
    ]

def create_cnc_machine(device_id: str = "Machine02_CNC"):
    state = {
        "status": 1,
        "spindle_rpm": 3600,
        "feed_rate_mm_min": 1200.0,
        "tool_wear_pct": 14.5,
        "coolant_flow_l_min": 18.2,
        "axis_x_pos": 150.25,
        "axis_y_pos": 84.10,
    }
    metrics = [
        m("Status", DataType.INT32, state["status"]),
        m("Spindle_RPM", DataType.INT32, state["spindle_rpm"]),
        m("Feed_Rate_mm_min", DataType.FLOAT, state["feed_rate_mm_min"]),
        m("Tool_Wear_Pct", DataType.FLOAT, state["tool_wear_pct"]),
        m("Coolant_Flow_L_min", DataType.FLOAT, state["coolant_flow_l_min"]),
        m("Axis_X_Pos_mm", DataType.FLOAT, state["axis_x_pos"]),
        m("Axis_Y_Pos_mm", DataType.FLOAT, state["axis_Y_pos"]),
    ]
    return Device(device_id=device_id, metrics=metrics), state

def update_cnc_machine(state: dict) -> list[Metric]:
    is_running = random.random() > 0.10
    state["status"] = 1 if is_running else 0
    if is_running:
        state["spindle_rpm"] = random.randint(3400, 4200)
        state["feed_rate_mm_min"] = round(random.uniform(1150.0, 1350.0), 1)
        state["coolant_flow_l_min"] = round(random.uniform(16.5, 20.0), 2)
        state["tool_wear_pct"] = round(min(100.0, state["tool_wear_pct"] + 0.01), 2)
        state["axis_x_pos"] = round(random.uniform(10.0, 500.0), 2)
        state["axis_y_pos"] = round(random.uniform(10.0, 300.0), 2)
    else:
        state["spindle_rpm"] = 0
        state["feed_rate_mm_min"] = 0.0
        state["coolant_flow_l_min"] = 0.0

    return [
        m("Status", DataType.INT32, state["status"]),
        m("Spindle_RPM", DataType.INT32, state["spindle_rpm"]),
        m("Feed_Rate_mm_min", DataType.FLOAT, state["feed_rate_mm_min"]),
        m("Tool_Wear_Pct", DataType.FLOAT, state["tool_wear_pct"]),
        m("Coolant_Flow_L_min", DataType.FLOAT, state["coolant_flow_l_min"]),
        m("Axis_X_Pos_mm", DataType.FLOAT, state["axis_x_pos"]),
        m("Axis_Y_Pos_mm", DataType.FLOAT, state["axis_y_pos"]),
    ]

def create_packaging_line(device_id: str = "Machine03_Packaging"):
    state = {
        "status": 1,
        "conveyor_speed": 1.25,
        "carton_count": 890,
        "sealing_temp": 145.0,
        "glue_level_pct": 74.0,
        "jam_alarm": False,
    }
    metrics = [
        m("Status", DataType.INT32, state["status"]),
        m("Conveyor_Speed_m_s", DataType.FLOAT, state["conveyor_speed"]),
        m("Carton_Count", DataType.INT64, state["carton_count"]),
        m("Sealing_Temp_C", DataType.FLOAT, state["sealing_temp"]),
        m("Glue_Level_Pct", DataType.FLOAT, state["glue_level_pct"]),
        m("Jam_Alarm", DataType.BOOLEAN, state["jam_alarm"]),
    ]
    return Device(device_id=device_id, metrics=metrics), state

def update_packaging_line(state: dict) -> list[Metric]:
    jam = random.random() < 0.05
    state["jam_alarm"] = jam
    is_running = (not jam) and (random.random() > 0.10)
    state["status"] = 1 if is_running else 0
    if is_running:
        state["carton_count"] += random.randint(1, 4)
        state["conveyor_speed"] = round(random.uniform(1.15, 1.40), 2)
        state["sealing_temp"] = round(random.uniform(142.0, 148.0), 1)
        state["glue_level_pct"] = max(5.0, round(state["glue_level_pct"] - 0.03, 2))
    else:
        state["conveyor_speed"] = 0.0
        state["sealing_temp"] = round(max(50.0, state["sealing_temp"] - 1.0), 1)

    return [
        m("Status", DataType.INT32, state["status"]),
        m("Conveyor_Speed_m_s", DataType.FLOAT, state["conveyor_speed"]),
        m("Carton_Count", DataType.INT64, state["carton_count"]),
        m("Sealing_Temp_C", DataType.FLOAT, state["sealing_temp"]),
        m("Glue_Level_Pct", DataType.FLOAT, state["glue_level_pct"]),
        m("Jam_Alarm", DataType.BOOLEAN, state["jam_alarm"]),
    ]

def main():
    print("=" * 70)
    print("  Sparkplug B Industrial Factory Simulator")
    print("=" * 70)
    node_metrics = [
        m("CPU_Load", DataType.FLOAT, 14.2),
        m("Line_Status", DataType.STRING, "NORMAL_OPERATION"),
    ]
    edge_node = EdgeNode(group_id=GROUP_ID, edge_node_id=EDGE_NODE_ID, metrics=node_metrics)

    dev1, state1 = create_stamping_press()
    dev2, state2 = create_cnc_machine()
    dev3, state3 = create_packaging_line()

    edge_node.register(dev1)
    edge_node.register(dev2)
    edge_node.register(dev3)

    print(f"Connecting to broker at {BROKER_HOST}:{BROKER_PORT}...")
    edge_node.connect(host=BROKER_HOST, port=BROKER_PORT)
    time.sleep(1.5)
    print("Connected! Streaming live telemetry every 2 seconds. Press Ctrl+C to stop.\n")

    try:
        iteration = 1
        while True:
            m1 = update_stamping_press(state1)
            edge_node.update_device("Machine01_Stamping", m1)
            m2 = update_cnc_machine(state2)
            edge_node.update_device("Machine02_CNC", m2)
            m3 = update_packaging_line(state3)
            edge_node.update_device("Machine03_Packaging", m3)

            print(f"[{time.strftime('%H:%M:%S')}] Cycle #{iteration}:")
            print(f"  • Stamping : Status={state1['status']} | Bar={state1['hydraulic_pressure']} | Temp={state1['die_temp']}°C")
            print(f"  • CNC      : Status={state2['status']} | RPM={state2['spindle_rpm']} | Wear={state2['tool_wear_pct']}%")
            print(f"  • Packaging: Status={state3['status']} | Speed={state3['conveyor_speed']}m/s | Cartons={state3['carton_count']}")
            iteration += 1
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopping...")
        edge_node.disconnect()

if __name__ == "__main__":
    main()
```

### 6.5 `simulator/factory_api_server.py` (Architecture A)
```python
"""Simulated Factory API Server."""

import datetime
import random
from fastapi import FastAPI, Header, HTTPException, status
import uvicorn

app = FastAPI(title="Simulated Factory MES API", version="1.0.0")
EXPECTED_API_KEY = "plant-secret-api-token-2026"

FACTORY_STATE = {
    "M01": {"machine_id": "M01", "status": 1, "hydraulic_pressure": 182.5, "die_temp": 64.0, "stroke_count": 1450},
    "M02": {"machine_id": "M02", "status": 1, "spindle_rpm": 3800, "feed_rate": 1250.0, "tool_wear": 15.2},
    "M03": {"machine_id": "M03", "status": 1, "conveyor_speed": 1.30, "carton_count": 920, "jam_alarm": False},
}

def verify_api_key(x_api_key: str | None = Header(None)):
    if x_api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid X-API-KEY header")

@app.get("/api/v1/factory/machines/telemetry", dependencies=[verify_api_key])
async def get_machines_telemetry():
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    telemetry_list = []
    for m_id, s in FACTORY_STATE.items():
        s["status"] = 1 if random.random() > 0.10 else 0
        telemetry_list.append({
            "machine_id": m_id,
            "status": s["status"],
            "timestamp": now_utc,
            "parameters": {k: v for k, v in s.items() if k not in ("machine_id", "status")},
        })
    return {"status": "success", "plant_id": "Plant1", "line_id": "Line1", "data": telemetry_list}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8005, log_level="warning")
```

### 6.6 `src/factory_backend/core/config.py`
```python
"""Core configuration module loading environment variables via Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    POSTGRES_USER: str = "factory_user"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "factory_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5434
    DATABASE_URL: str = "postgresql+asyncpg://factory_user@/factory_db?host=/tmp&port=5434"

    FACTORY_API_BASE_URL: str = "http://localhost:8005/api/v1"
    FACTORY_API_KEY: str = "plant-secret-api-token-2026"
    FACTORY_API_POLL_INTERVAL_SECONDS: float = 3.0

    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = "backend_service"
    MQTT_PASSWORD: str = "backend_pass_secure"
    MQTT_CLIENT_ID: str = "factory_backend_subscriber"
    MQTT_TOPIC_TELEMETRY: str = "plant/+/+/telemetry"
    MQTT_TOPIC_SPARKPLUG: str = "spBv1.0/+/+/+"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
```

### 6.7 `src/factory_backend/db/session.py`
```python
"""Async SQLAlchemy session and engine management."""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from factory_backend.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True, poolclass=NullPool)
async_session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 6.8 `src/factory_backend/db/models.py`
```python
"""Database models with JSONB for dynamic machine telemetry."""

import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from factory_backend.db.session import Base

class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False, default="Plant1")
    line_id: Mapped[str] = mapped_column(String(50), nullable=False, default="Line1")
    machine_type: Mapped[str] = mapped_column(String(50), nullable=False)
    plc_model: Mapped[str] = mapped_column(String(50), nullable=True, default="Siemens S7-1500")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    telemetry_records: Mapped[list["MachineTelemetry"]] = relationship("MachineTelemetry", back_populates="machine", cascade="all, delete-orphan")
    shift_summaries: Mapped[list["MachineShiftSummary"]] = relationship("MachineShiftSummary", back_populates="machine", cascade="all, delete-orphan")

class MachineTelemetry(Base):
    __tablename__ = "machine_telemetry"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(String(50), ForeignKey("machines.id"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    received_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    machine: Mapped["Machine"] = relationship("Machine", back_populates="telemetry_records")
    __table_args__ = (
        Index("idx_telemetry_machine_timestamp", "machine_id", "timestamp"),
        Index("idx_telemetry_parameters_gin", "parameters", postgresql_using="gin"),
    )

class MachineShiftSummary(Base):
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
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    machine: Mapped["Machine"] = relationship("Machine", back_populates="shift_summaries")
```

### 6.9 `src/factory_backend/schemas/telemetry.py`
```python
"""Pydantic schemas for data validation and normalization."""

import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator

class RawTelemetryPayload(BaseModel):
    machine_id: str
    status: int | bool
    timestamp: datetime.datetime | int | float | str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v: Any) -> int:
        if isinstance(v, bool):
            return 1 if v else 0
        if isinstance(v, int | float):
            return 1 if int(v) > 0 else 0
        if isinstance(v, str):
            if v.strip().lower() in ("running", "1", "true", "on", "ok"):
                return 1
            return 0
        return 0

class NormalizedTelemetry(BaseModel):
    machine_id: str
    status: int
    source_type: str
    timestamp: datetime.datetime
    received_at: datetime.datetime
    parameters: dict[str, Any]
    ingestion_latency_ms: float = 0.0

class MachineResponse(BaseModel):
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
    machine: MachineResponse
    latest_telemetry: NormalizedTelemetry | None
```

### 6.10 `src/factory_backend/pipeline/processor.py`
```python
"""Common Data Ingestion Pipeline."""

import datetime
from typing import Any
from sqlalchemy import update
from factory_backend.db.models import Machine, MachineTelemetry
from factory_backend.db.session import async_session_factory
from factory_backend.schemas.telemetry import NormalizedTelemetry, RawTelemetryPayload

class TelemetryPipeline:
    def __init__(self):
        self._latest_cache: dict[str, NormalizedTelemetry] = {}
        self._listeners: set[Any] = set()

    def register_listener(self, listener):
        self._listeners.add(listener)

    def unregister_listener(self, listener):
        self._listeners.discard(listener)

    def get_latest_cached(self, machine_id: str) -> NormalizedTelemetry | None:
        return self._latest_cache.get(machine_id)

    def normalize(self, raw: RawTelemetryPayload, source_type: str) -> NormalizedTelemetry:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        if raw.timestamp is None:
            event_time = now_utc
        elif isinstance(raw.timestamp, int | float):
            event_time = datetime.datetime.fromtimestamp((raw.timestamp / 1000.0) if raw.timestamp > 1e11 else raw.timestamp, tz=datetime.timezone.utc)
        elif isinstance(raw.timestamp, str):
            try:
                event_time = datetime.datetime.fromisoformat(raw.timestamp)
                if event_time.tzinfo is None:
                    event_time = event_time.replace(tzinfo=datetime.timezone.utc)
            except Exception:
                event_time = now_utc
        else:
            event_time = raw.timestamp if raw.timestamp.tzinfo else raw.timestamp.replace(tzinfo=datetime.timezone.utc)

        latency_ms = max(0.0, (now_utc - event_time).total_seconds() * 1000.0)
        cleaned_params = {k.strip().replace(" ", "_"): v for k, v in raw.parameters.items()}

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
        raw_payload = RawTelemetryPayload(**raw_data)
        normalized = self.normalize(raw_payload, source_type=source_type)
        self._latest_cache[normalized.machine_id] = normalized

        async with async_session_factory() as session:
            async with session.begin():
                record = MachineTelemetry(
                    machine_id=normalized.machine_id,
                    source_type=normalized.source_type,
                    status=normalized.status,
                    parameters=normalized.parameters,
                    timestamp=normalized.timestamp,
                    received_at=normalized.received_at,
                )
                session.add(record)
                await session.execute(
                    update(Machine)
                    .where(Machine.id == normalized.machine_id)
                    .values(status=normalized.status, updated_at=normalized.received_at)
                )

        for listener in list(self._listeners):
            try:
                await listener(normalized)
            except Exception:
                pass

        return normalized

pipeline = TelemetryPipeline()
```

### 6.11 `src/factory_backend/integrations/api_poller.py` (Architecture A)
```python
"""Architecture A: Factory API Poller worker."""

import asyncio
import logging
import httpx
from factory_backend.core.config import settings
from factory_backend.pipeline.processor import pipeline

logger = logging.getLogger("factory_backend.integrations.api_poller")

class FactoryApiPoller:
    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self.endpoint = f"{settings.FACTORY_API_BASE_URL}/factory/machines/telemetry"
        self.headers = {
            "X-API-KEY": settings.FACTORY_API_KEY,
            "Accept": "application/json",
            "User-Agent": "FactoryBackendIntegration/1.0",
        }
        self.poll_interval = settings.FACTORY_API_POLL_INTERVAL_SECONDS

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"Factory API Poller started. Target: {self.endpoint}")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _poll_loop(self):
        async with httpx.AsyncClient(timeout=4.0) as client:
            while self._running:
                try:
                    res = await client.get(self.endpoint, headers=self.headers)
                    if res.status_code == 200:
                        payload = res.json()
                        for item in payload.get("data", []):
                            await pipeline.process(raw_data=item, source_type="api")
                    elif res.status_code == 401:
                        logger.error("Authentication failed: Invalid X-API-KEY")
                except httpx.ConnectError:
                    logger.debug("Factory API server offline. Retrying...")
                except Exception as ex:
                    logger.error(f"Error in poller: {ex}")
                await asyncio.sleep(self.poll_interval)

api_poller = FactoryApiPoller()
```

### 6.12 `src/factory_backend/integrations/mqtt_listener.py` (Architecture B)
```python
"""Architecture B: MQTT Ingestion Subscriber."""

import asyncio
import json
import logging
import paho.mqtt.client as mqtt
from factory_backend.core.config import settings
from factory_backend.pipeline.processor import pipeline

logger = logging.getLogger("factory_backend.integrations.mqtt")

class MqttListener:
    def __init__(self):
        self.client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID, clean_session=True)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self._loop: asyncio.AbstractEventLoop | None = None

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
            client.subscribe(settings.MQTT_TOPIC_TELEMETRY, qos=1)
        else:
            logger.error(f"MQTT connection refused with code {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    pipeline.process(raw_data=data, source_type="mqtt_json"),
                    self._loop,
                )
        except Exception as ex:
            logger.warning(f"Failed to process message: {ex}")

    def start(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        try:
            self.client.connect_async(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60)
            self.client.loop_start()
        except Exception as ex:
            logger.error(f"Could not connect to MQTT: {ex}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

mqtt_listener = MqttListener()
```

### 6.13 `src/factory_backend/api/router.py`
```python
"""FastAPI REST & WebSocket Endpoints."""

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
    return {"status": "ok", "service": "factory_backend"}

@router.get("/readyz")
async def readiness_check(session: AsyncSession = Depends(get_db_session)):
    try:
        await session.execute(select(1))
        return {"status": "ready", "database": "connected"}
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(ex))

@router.get("/machines", response_model=list[MachineResponse])
async def list_machines(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(Machine).order_by(Machine.id))
    return result.scalars().all()

@router.get("/machines/{machine_id}", response_model=LatestMachineState)
async def get_machine_detail(machine_id: str, session: AsyncSession = Depends(get_db_session)):
    machine = await session.get(Machine, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

    cached_telemetry = pipeline.get_latest_cached(machine_id)
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
            )

    return LatestMachineState(machine=MachineResponse.model_validate(machine), latest_telemetry=cached_telemetry)

@router.get("/machines/{machine_id}/history")
async def get_machine_history(machine_id: str, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0), session: AsyncSession = Depends(get_db_session)):
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

@router.websocket("/ws/live")
async def live_telemetry_ws(websocket: WebSocket, machine_id: str | None = None):
    await websocket.accept()
    async def on_telemetry(telemetry: NormalizedTelemetry):
        if machine_id and telemetry.machine_id != machine_id:
            return
        await websocket.send_json({"event": "telemetry_update", "data": telemetry.model_dump(mode="json")})

    pipeline.register_listener(on_telemetry)
    try:
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        pipeline.unregister_listener(on_telemetry)
```

### 6.14 `src/factory_backend/api/main.py`
```python
"""FastAPI Application Entry Point."""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from factory_backend.api.router import router
from factory_backend.core.config import settings
from factory_backend.integrations.api_poller import api_poller
from factory_backend.integrations.mqtt_listener import mqtt_listener

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    await api_poller.start()
    mqtt_listener.start(loop)
    yield
    await api_poller.stop()
    mqtt_listener.stop()

app = FastAPI(
    title="Industrial Factory Data Integration Backend",
    description="Dual-Architecture (HTTP API & MQTT) Telemetry Backend for Mobile SCADA Applications",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

def start():
    uvicorn.run("factory_backend.api.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=False)

if __name__ == "__main__":
    start()
```

### 6.15 `tests/test_integration.py`
```python
"""Automated Integration Test Suite."""

import datetime
import pytest
from httpx import ASGITransport, AsyncClient
from factory_backend.api.main import app
from factory_backend.pipeline.processor import pipeline

@pytest.mark.asyncio
async def test_pipeline_normalization_and_validation():
    payload = {
        "machine_id": "M01",
        "status": True,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "parameters": {"hydraulic_pressure": 185.2, "die_temp": 65.4, "stroke_count": 1420},
    }
    normalized = await pipeline.process(raw_data=payload, source_type="api")
    assert normalized.machine_id == "M01"
    assert normalized.status == 1
    assert normalized.parameters["hydraulic_pressure"] == 185.2

@pytest.mark.asyncio
async def test_mobile_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/healthz")
        assert res.status_code == 200
        res_m = await client.get("/api/v1/machines")
        assert res_m.status_code == 200
        assert len(res_m.json()) >= 3
```
