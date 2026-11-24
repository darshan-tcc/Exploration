"""Industrial Factory Line Simulation using Eclipse Sparkplug B.

Simulates a production line with multiple machines:
  - Machine01: Stamping Press
  - Machine02: CNC Milling Center
  - Machine03: Packaging & Conveyor

Publishes via Sparkplug B (Protobuf binary) to Mosquitto.
Ignition MQTT Engine automatically discovers all nodes, devices, and tags.
"""

import random
import time
from pysparkplug import DataType, Device, EdgeNode, Metric, get_current_timestamp

GROUP_ID = "Plant1"
EDGE_NODE_ID = "Line1"
BROKER_HOST = "localhost"
BROKER_PORT = 1883


def m(name: str, datatype: DataType, value) -> Metric:
    """Helper to create a Metric with current timestamp."""
    return Metric(timestamp=get_current_timestamp(), name=name, datatype=datatype, value=value)


def create_machine_device(device_id: str) -> tuple[Device, dict]:
    """Create a Sparkplug B Device with initial metrics."""
    state = {
        "production_count": 0,
        "running": True,
        "temperature": 35.0,
        "pressure": 5.5,
        "motor_rpm": 1400,
    }

    metrics = [
        m("Temperature", DataType.FLOAT, state["temperature"]),
        m("Pressure", DataType.FLOAT, state["pressure"]),
        m("Motor_RPM", DataType.INT32, state["motor_rpm"]),
        m("Running", DataType.BOOLEAN, state["running"]),
        m("Production_Count", DataType.INT64, state["production_count"]),
    ]

    device = Device(device_id=device_id, metrics=metrics)
    return device, state


def update_machine_state(state: dict, machine_type: str) -> list[Metric]:
    """Generate dynamic telemetry changes for a machine."""
    running = random.random() > 0.15
    state["running"] = running

    if running:
        state["production_count"] += random.randint(1, 3)
        if machine_type == "stamping":
            state["temperature"] = round(random.uniform(45.0, 78.0), 2)
            state["pressure"] = round(random.uniform(5.5, 7.8), 2)
            state["motor_rpm"] = random.randint(1100, 1600)
        elif machine_type == "cnc":
            state["temperature"] = round(random.uniform(38.0, 68.0), 2)
            state["pressure"] = round(random.uniform(4.0, 6.2), 2)
            state["motor_rpm"] = random.randint(2800, 4200)
        else:  # packaging
            state["temperature"] = round(random.uniform(28.0, 48.0), 2)
            state["pressure"] = round(random.uniform(3.5, 5.0), 2)
            state["motor_rpm"] = random.randint(800, 1200)
    else:
        state["motor_rpm"] = 0
        state["temperature"] = max(25.0, round(state["temperature"] - 1.5, 2))
        state["pressure"] = 4.0

    return [
        m("Temperature", DataType.FLOAT, state["temperature"]),
        m("Pressure", DataType.FLOAT, state["pressure"]),
        m("Motor_RPM", DataType.INT32, state["motor_rpm"]),
        m("Running", DataType.BOOLEAN, state["running"]),
        m("Production_Count", DataType.INT64, state["production_count"]),
    ]


def main():
    print("=" * 65)
    print("  Sparkplug B Industrial Multi-Machine Factory Simulator")
    print("=" * 65)
    print(f"Group ID:      {GROUP_ID}")
    print(f"Edge Node ID:  {EDGE_NODE_ID}")
    print(f"Broker:        {BROKER_HOST}:{BROKER_PORT}")
    print("Devices:       Machine01 (Stamping), Machine02 (CNC), Machine03 (Packaging)")
    print("-" * 65)

    # Edge Node Metrics (system level health)
    node_metrics = [
        m("CPU_Load", DataType.FLOAT, 12.5),
        m("Line_Status", DataType.STRING, "NORMAL_OPERATION"),
    ]

    edge_node = EdgeNode(group_id=GROUP_ID, edge_node_id=EDGE_NODE_ID, metrics=node_metrics)

    # Define 3 Machines
    machines = {
        "Machine01_Stamping": create_machine_device("Machine01_Stamping"),
        "Machine02_CNC": create_machine_device("Machine02_CNC"),
        "Machine03_Packaging": create_machine_device("Machine03_Packaging"),
    }

    # Register devices to the Edge Node
    for dev_id, (device, _) in machines.items():
        edge_node.register(device)
        print(f"Registered Device: {dev_id}")

    # Connect to Broker (Sends NBIRTH and DBIRTH automatically)
    print(f"\nConnecting to broker at {BROKER_HOST}:{BROKER_PORT}...")
    edge_node.connect(host=BROKER_HOST, port=BROKER_PORT)
    time.sleep(1.5)  # Wait for NBIRTH and DBIRTH handshake with Ignition
    print("Connected! Sent NBIRTH and DBIRTH (Auto-discovery triggered in Ignition).")
    print("Streaming live telemetry every 2 seconds. Press Ctrl+C to stop.\n")

    try:
        iteration = 1
        while True:
            print(f"[{time.strftime('%H:%M:%S')}] Cycle #{iteration}:")
            for dev_id, (_, state) in machines.items():
                m_type = "stamping" if "Stamping" in dev_id else ("cnc" if "CNC" in dev_id else "packaging")
                updated_metrics = update_machine_state(state, m_type)
                edge_node.update_device(dev_id, updated_metrics)
                status = "RUNNING" if state["running"] else "IDLE"
                print(f"  • {dev_id:20} -> {status:7} | RPM: {state['motor_rpm']:4} | Temp: {state['temperature']}°C | Parts: {state['production_count']}")

            # Update Node CPU metric occasionally
            cpu_val = round(random.uniform(8.0, 25.0), 1)
            edge_node.update([m("CPU_Load", DataType.FLOAT, cpu_val)])

            iteration += 1
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopping factory simulation...")
        edge_node.disconnect()
        print("Disconnected gracefully (sent DDEATH/NDEATH certificates).")


if __name__ == "__main__":
    main()
