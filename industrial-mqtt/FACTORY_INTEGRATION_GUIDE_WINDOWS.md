# Factory Data Integration & Ignition MQTT — Complete Windows Operations Handbook

> **Architecture Summary:** Single unified industrial architecture where **all factory machines connect to Ignition SCADA via MQTT (Sparkplug B / Cirrus Link)**. Ignition acts as the central industrial broker and tag engine. Our modular FastAPI backend subscribes to Ignition's telemetry, normalizes parameters, persists to PostgreSQL with dynamic **JSONB**, and exposes clean REST & WebSocket endpoints for mobile applications (Flutter / React Native).
> *(No standalone Mosquitto or separate HTTP API polling required).*

---

## 1. Official Windows Download Links

All software components used in this project run natively on Microsoft Windows:

| Software / Component | Official Windows Download Link | Installation Format / Notes |
| :--- | :--- | :--- |
| **Ignition SCADA Gateway (8.1 / 8.3)** | [Inductive Automation Downloads](https://inductiveautomation.com/downloads/) | `ignition-8.x.x-windows-x64-installer.exe` (Runs natively as a Windows Service). |
| **Ignition Designer Launcher** | Downloaded from your running Gateway: `http://localhost:8088` (Home ➔ **Get Designer**) or [Inductive Automation Downloads](https://inductiveautomation.com/downloads/) | `designerlauncher.exe` (Desktop app for live gauges, tags, and HMI screens). |
| **Cirrus Link MQTT Distributor Module** | [Cirrus Link Module Downloads](https://sales.cirrus-link.com/download-modules/) | `MQTT-Distributor-signed.modl` (Turns Ignition Gateway into a full MQTT Broker on port 1883). |
| **Cirrus Link MQTT Engine Module** | [Cirrus Link Module Downloads](https://sales.cirrus-link.com/download-modules/) | `MQTT-Engine-signed.modl` (Consumes Sparkplug B & auto-creates SCADA tags). |
| **PostgreSQL Database for Windows** | [PostgreSQL Windows Installer (EDB)](https://www.postgresql.org/download/windows/) | `postgresql-16.x-windows-x64.exe` (Standard installer; runs as Windows Service). |
| **Python (>= 3.12) & `pip`** | [Python for Windows](https://www.python.org/downloads/windows/) | Official Python installer. Standard `pip install -r requirements.txt` works out of the box (`uv` is completely optional). |

---

## 2. Single Streamlined Architecture & Port Map

```mermaid
flowchart TD
    subgraph EdgeMachines["Factory Floor & Simulators (Python on Windows)"]
        Stamping["Machine 01: Stamping Press<br/>(Pressure, Die Temp, Tonnage, Stroke Count)"]
        CNC["Machine 02: CNC Milling Center<br/>(Spindle RPM, Feed Rate, Coolant, Tool Wear)"]
        Packaging["Machine 03: Packaging & Conveyor<br/>(Speed, Carton Count, Sealing Temp, Jam)"]
        Sim["Sparkplug B Simulator<br/>(simulator\sparkplug_factory.py)"]
        Stamping --> Sim
        CNC --> Sim
        Packaging --> Sim
    end

    subgraph IgnitionPlatform["Ignition SCADA All-In-One Platform (Windows)"]
        Distributor["Ignition MQTT Distributor<br/>(Built-in MQTT Broker on Port: 1883)"]
        Engine["Ignition MQTT Engine<br/>(Auto-discovers Nodes, Devices & Tags)"]
        GatewayUI["Gateway Web Interface<br/>http://localhost:8088"]
        Designer["Ignition Designer Desktop App<br/>(Perspective HMI, Live Gauges & Controls)"]

        Distributor -->|Internal Loopback| Engine
        Engine -->|Live Real-Time Tags| Designer
        GatewayUI --- Distributor
        GatewayUI --- Engine
    end

    subgraph BackendApp["Custom Python Backend & Storage"]
        BackendWorker["FastAPI Backend Ingestion Worker<br/>(Subscribes to Ignition MQTT on Port 1883)"]
        Pipeline["Common Ingestion Pipeline<br/>(Validate -> Normalize -> UTC Align -> Latency Calc)"]
        HotCache[("In-Memory Hot Cache<br/>O(1) Instant State Lookup")]
        PG[("PostgreSQL 16 Database<br/>Port: 5432 (JSONB Dynamic Parameters)")]
        REST["FastAPI REST Endpoints<br/>Port: 8000 (Swagger: /docs)"]
        WS["WebSocket Live Stream Hub<br/>/api/v1/ws/live"]

        BackendWorker --> Pipeline
        Pipeline --> HotCache
        Pipeline -->|Async Batch Insert| PG
        Pipeline -->|Push Broadcast| WS
        HotCache --> REST
        PG --> REST
    end

    subgraph MobileConsumers["Mobile & Web Applications"]
        Mobile["Mobile Application<br/>(Flutter / React Native)<br/>- Live Gauges & Machine Status<br/>- Today's OEE & Shift Production<br/>- Historical Trend Charts"]
    end

    Sim -->|Sparkplug B Protobuf :1883| Distributor
    Distributor -->|Live Telemetry Feed| BackendWorker
    REST -->|HTTP JSON API| Mobile
    WS -->|Real-Time Telemetry Stream| Mobile
```

---

## 3. Step-by-Step Installation on Windows

### Step 1: Install Python Dependencies using `pip`
1. Download Python (>= 3.12) from [python.org](https://www.python.org/downloads/windows/).
2. Run installer and ensure you check: **`[x] Add python.exe to PATH`**.
3. Open **Windows PowerShell** or **Command Prompt** inside your `industrial-mqtt` folder:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   *(Note: `uv` is optional. Standard `pip` installs all required packages cleanly).*

### Step 2: Install PostgreSQL on Windows
1. Download installer from [EnterpriseDB PostgreSQL](https://www.postgresql.org/download/windows/).
2. Follow wizard:
   - Accept default components (Server, pgAdmin, Command Line Tools).
   - Enter password for `postgres` (e.g. `factory_secure_pass_2026`).
   - Port: `5432`.
3. PostgreSQL starts automatically as a background **Windows Service**.

### Step 3: Install Ignition Gateway on Windows
1. Download `ignition-8.x.x-windows-x64-installer.exe` from [Inductive Automation](https://inductiveautomation.com/downloads/).
2. Double-click installer ➔ Typical Installation ➔ Click Install.
3. Open your browser to: **[http://localhost:8088](http://localhost:8088)**.
4. Follow commissioning wizard:
   - Choose **Maker Edition** (free for personal use) or **Standard Trial** (renewable 2-hour trial).
   - Create Admin username (e.g. `admin`) and password.
   - Click **Start Gateway**.

---

## 4. Installing & Enabling MQTT Modules in Ignition

In this architecture, Ignition runs both the **MQTT Broker** and the **SCADA Tag Engine**.

### 4.1 Step 1: Download & Upload Modules
1. Download from [Cirrus Link Module Downloads](https://sales.cirrus-link.com/download-modules/):
   - `MQTT-Distributor-signed.modl`
   - `MQTT-Engine-signed.modl`
2. In browser at `http://localhost:8088`, go to **Config ➔ System ➔ Modules**.
3. Click **Install or Upgrade a Module...** at the bottom.
4. Upload `MQTT-Distributor-signed.modl` ➔ accept EULA ➔ Confirm.
5. Upload `MQTT-Engine-signed.modl` ➔ accept EULA ➔ Confirm.
6. Verify both show green status: **Running**.

### 4.2 Step 2: Verify Ignition MQTT Broker Credentials
1. Go to **Config ➔ MQTT DISTRIBUTOR ➔ Settings**.
2. Notice broker port is `1883`.
3. Click **Users**:
   - Default credentials created by Distributor are:
     - **Username:** `admin`
     - **Password:** `changeme`
4. Ignition is now running a full MQTT broker on port 1883!

### 4.3 Step 3: Verify MQTT Engine Connection
1. Go to **Config ➔ MQTT ENGINE ➔ Settings ➔ Servers**.
2. Notice the pre-configured connection to `tcp://localhost:1883`.
3. Status shows **Connected** with a green checkmark.

---

## 5. Launching Designer on Windows & Visualizing Live Gauges

### 5.1 Launching Designer
1. On your running Gateway (`http://localhost:8088`), go to the **Home** tab.
2. Under **Get Designer**, download `designerlauncher.exe`.
3. Open Designer Launcher from your Start Menu or Desktop.
4. Click **Launch** next to `http://localhost:8088` and log in.
5. Click **New Project** ➔ Name it `Factory_Overview` ➔ Create Project.

### 5.2 Locating the Auto-Discovered Tags
1. In Designer, open the **Tag Browser** on the left.
2. Switch dropdown from `[default]` to **`[MQTT Engine]`**.
3. In PowerShell, start the multi-machine simulator:
   ```powershell
   python simulator\sparkplug_factory.py
   ```
4. Look at Designer: The tree appears instantly with live updating values:
   ```text
   [MQTT Engine]
     └── Edge Nodes
           └── Plant1
                 └── Line1
                       ├── Machine01_Stamping  (Hydraulic Pressure, Die Temp, Tonnage, Stroke Count)
                       ├── Machine02_CNC       (Spindle RPM, Feed Rate, Tool Wear, Coolant Flow)
                       └── Machine03_Packaging (Conveyor Speed, Carton Count, Sealing Temp, Jam Alarm)
   ```

### 5.3 Building a Live Perspective Dashboard
1. In **Project Browser**, expand **Perspective ➔ Views** ➔ Right-click **New View...** ➔ `Machine_Overview`.
2. From the Component Palette, drag a **Gauge** component onto the canvas.
3. In the PROPS panel on the bottom-right, find `value` and click the **Binding / Chain icon**.
4. Select **Tag** and browse to:
   `[MQTT Engine]Edge Nodes/Plant1/Line1/Machine01_Stamping/Hydraulic_Pressure_Bar`
5. Set `minValue: 0`, `maxValue: 250`, `units: Bar`.
6. Drag a **Label** component for status, bind text to `.../Machine01_Stamping/Status`, and add a Map transform (`1 -> "RUNNING"`, `0 -> "STOPPED"`).
7. The gauge needle and status animate live on your screen!

---

## 6. How the Code Works & How Parameters Map to the Screen

```mermaid
sequenceDiagram
    autonumber
    participant Py as Python on Windows (sparkplug_factory.py)
    participant Dist as Ignition MQTT Distributor (:1883)
    participant Eng as Ignition MQTT Engine
    participant Des as Ignition Designer (Perspective HMI)
    participant BE as FastAPI Backend & PostgreSQL

    Py->>Py: state["hydraulic_pressure"] = round(random.uniform(175.0, 195.0), 1) -> 184.2
    Py->>Dist: Publish DDATA (Protobuf: Hydraulic_Pressure_Bar = 184.2)
    Dist->>Eng: Internal message loopback inside Ignition Gateway
    Eng->>Eng: Unpacks Protobuf & updates tag [MQTT Engine].../Hydraulic_Pressure_Bar
    Eng->>Des: Pushes tag change event to Perspective Gauge
    Des->>Des: Gauge needle animates smoothly to 184.2 Bar!

    Note over Py,BE: Simultaneously to our Backend Pipeline:
    Dist->>BE: Async MQTT Subscriber receives telemetry
    BE->>BE: Normalizes, validates & stores in PostgreSQL (JSONB parameters)
    BE->>BE: Broadcasts live state to Mobile via WebSocket /api/v1/ws/live
```

---

## 7. Windows Commands Quick Reference

Open **PowerShell** or **Command Prompt**:

| Action | Windows PowerShell / CMD |
| :--- | :--- |
| **Activate Python Virtualenv** | `.\.venv\Scripts\Activate.ps1` |
| **Install Dependencies** | `pip install -r requirements.txt` |
| **Check Ignition Port 1883** | `netstat -ano | findstr 1883` |
| **Start Ignition Service** | `net start Ignition` *(or use Windows Services app `services.msc`)* |
| **Stop Ignition Service** | `net stop Ignition` |
| **Start Backend API Server** | `python -m factory_backend.api.main` |
| **Run Sparkplug B Simulation** | `python simulator\sparkplug_factory.py` |
| **Run Automated Tests** | `pytest tests\test_integration.py -v` |
| **Open Backend Swagger UI** | In browser: **`http://localhost:8000/docs`** |
| **Open Ignition Gateway Web** | In browser: **`http://localhost:8088`** |

---

## 8. Complete Source Code & File Locations

Below is the directory structure and source code for every file in the project. Place these files inside your `industrial-mqtt\` directory on Windows:

```text
industrial-mqtt\
├── .env
├── requirements.txt
├── pyproject.toml
├── pytest.ini
├── FACTORY_INTEGRATION_GUIDE_WINDOWS.md
├── simulator\
│   └── sparkplug_factory.py      (Sparkplug B Protobuf publisher for Ignition)
├── tests\
│   └── test_integration.py      (Pytest automated integration test suite)
└── src\factory_backend\
    ├── core\config.py            (Settings & .env loader)
    ├── db\
    │   ├── session.py            (Async PostgreSQL engine)
    │   └── models.py             (SQLAlchemy tables + JSONB)
    ├── schemas\telemetry.py      (Pydantic validation & normalization)
    ├── pipeline\processor.py     (Common ingestion pipeline & WebSocket hub)
    ├── integrations\
    │   └── mqtt_listener.py      (Ignition MQTT subscriber)
    └── api\
        ├── router.py             (REST & WebSocket endpoints)
        └── main.py               (FastAPI app & lifespan)
```

### 8.1 `requirements.txt`
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

### 8.2 Windows `.env` File
```ini
ENVIRONMENT=development
LOG_LEVEL=INFO
APP_HOST=0.0.0.0
APP_PORT=8000

# PostgreSQL on Windows (default port 5432)
POSTGRES_USER=factory_user
POSTGRES_PASSWORD=factory_secure_pass_2026
POSTGRES_DB=factory_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://factory_user:factory_secure_pass_2026@localhost:5432/factory_db

# Architecture: Ignition MQTT Distributor Broker
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=admin
MQTT_PASSWORD=changeme
MQTT_CLIENT_ID=factory_backend_subscriber
MQTT_TOPIC_TELEMETRY=plant/+/+/telemetry
MQTT_TOPIC_SPARKPLUG=spBv1.0/+/+/+
```

### 8.3 `simulator/sparkplug_factory.py`
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
        m("Axis_Y_Pos_mm", DataType.FLOAT, state["axis_y_pos"]),
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
    print("  Sparkplug B Factory Line -> Ignition SCADA")
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

    print(f"Connecting to Ignition MQTT broker at {BROKER_HOST}:{BROKER_PORT}...")
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

### 8.4 `src/factory_backend/core/config.py`
```python
"""Core configuration module loading environment variables via Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    POSTGRES_USER: str = "factory_user"
    POSTGRES_PASSWORD: str = "factory_secure_pass_2026"
    POSTGRES_DB: str = "factory_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://factory_user:factory_secure_pass_2026@localhost:5432/factory_db"

    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = "admin"
    MQTT_PASSWORD: str = "changeme"
    MQTT_CLIENT_ID: str = "factory_backend_subscriber"
    MQTT_TOPIC_TELEMETRY: str = "plant/+/+/telemetry"
    MQTT_TOPIC_SPARKPLUG: str = "spBv1.0/+/+/+"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
```

### 8.5 `src/factory_backend/db/session.py`
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

### 8.6 `src/factory_backend/db/models.py`
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
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, default="ignition_mqtt")
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

### 8.7 `src/factory_backend/schemas/telemetry.py`
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
    source_type: str = "ignition_mqtt"
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

### 8.8 `src/factory_backend/pipeline/processor.py`
```python
"""Common Data Ingestion Pipeline & WebSocket Hub."""

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

    def normalize(self, raw: RawTelemetryPayload, source_type: str = "ignition_mqtt") -> NormalizedTelemetry:
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

    async def process(self, raw_data: dict[str, Any], source_type: str = "ignition_mqtt") -> NormalizedTelemetry:
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

### 8.9 `src/factory_backend/integrations/mqtt_listener.py`
```python
"""Ignition MQTT Ingestion Subscriber."""

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
        if settings.MQTT_USERNAME:
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self._loop: asyncio.AbstractEventLoop | None = None

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to Ignition MQTT Broker!")
            client.subscribe(settings.MQTT_TOPIC_TELEMETRY, qos=1)
        else:
            logger.error(f"Ignition MQTT connection refused with code {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    pipeline.process(raw_data=data, source_type="ignition_mqtt"),
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
            logger.error(f"Could not connect to Ignition MQTT broker: {ex}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

mqtt_listener = MqttListener()
```

### 8.10 `src/factory_backend/api/router.py`
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

### 8.11 `src/factory_backend/api/main.py`
```python
"""FastAPI Application Entry Point & Lifespan Management."""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from factory_backend.api.router import router
from factory_backend.core.config import settings
from factory_backend.integrations.mqtt_listener import mqtt_listener

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    mqtt_listener.start(loop)
    yield
    mqtt_listener.stop()

app = FastAPI(
    title="Factory Data Integration & Ignition MQTT Backend",
    description="Single Industrial MQTT Architecture Connected to Ignition SCADA for Mobile Applications",
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

### 8.12 `tests/test_integration.py`
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
    normalized = await pipeline.process(raw_data=payload, source_type="ignition_mqtt")
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
