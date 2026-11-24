# Industrial MQTT & SCADA Exploration

This project explores Industrial IoT (IIoT) telemetry streaming using **MQTT**, **Eclipse Mosquitto**, and **Inductive Automation's Ignition SCADA**.

## Architecture Overview

```
[ Edge Simulator ]                     [ MQTT Broker ]                   [ SCADA Gateway ]
 simulator/machine.py  ──(Port 1883)──>   Mosquitto    ──(MQTT Engine)──>  Ignition 8.3
  • Temperature                         localhost:1883                     • SCADA Tag Browser
  • Pressure                                                               • Vision HMI Window
  • Motor RPM                                                              • Tag Historian (SQLite)
  • Production Counts
```

## Getting Started

### 1. Requirements
- Python >= 3.13
- [`uv`](https://docs.astral.sh/uv/) package manager
- Eclipse Mosquitto broker running on `localhost:1883`

### 2. Install Dependencies
```bash
uv sync
```

### 3. Run the Machine Simulator
```bash
uv run python simulator/machine.py
```

### 4. Topic Structure (ISA-95 Unified Namespace)
- **Topic:** `plant/line1/machine01/telemetry`
- **QoS:** 1
- **Payload Format:** JSON
  ```json
  {
    "machine_id": "MACHINE-01",
    "temperature": 45.2,
    "pressure": 6.1,
    "motor_rpm": 1420,
    "running": true,
    "production_count": 12,
    "timestamp": 1795406499.4
  }
  ```

## Roadmap
- [x] Basic Mosquitto Pub/Sub & Telemetry Simulation
- [x] Ignition SCADA Integration (Cirrus Link MQTT Engine)
- [x] Real-time Vision HMI operator dashboard
- [ ] Sparkplug B Protocol implementation (Eclipse Tahu / Protobuf)
- [ ] Multi-machine concurrent simulation & OEE analytics
