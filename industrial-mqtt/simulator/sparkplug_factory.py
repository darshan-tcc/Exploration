"""Industrial Factory Line Simulation using Eclipse Sparkplug B.

Simulates a realistic production line with heterogeneous machines:
  1. Machine01_Stamping:
     - Hydraulic_Pressure (Bar), Die_Temp (°C), Stroke_Count, Tonnage (Tons), Lubrication_Level (%)
  2. Machine02_CNC:
     - Spindle_RPM, Feed_Rate (mm/min), Tool_Wear (%), Coolant_Flow (L/min), Axis_X_Pos, Axis_Y_Pos
  3. Machine03_Packaging:
     - Conveyor_Speed (m/s), Carton_Count, Sealing_Temp (°C), Glue_Level (%), Jam_Alarm (Bool)

Publishes via Sparkplug B (Protobuf binary) to Mosquitto.
Ignition MQTT Engine automatically discovers each device with its own distinct tag structure.
"""

import argparse
import os
import random
import time
from pysparkplug import DataType, Device, EdgeNode, Metric, get_current_timestamp

DEFAULT_GROUP_ID = os.getenv("SPARKPLUG_GROUP_ID", "Plant1")
DEFAULT_EDGE_NODE_ID = os.getenv("SPARKPLUG_NODE_ID", "Line1")
DEFAULT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
DEFAULT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))


def m(name: str, datatype: DataType, value) -> Metric:
    """Helper to create a Metric with current timestamp."""
    return Metric(timestamp=get_current_timestamp(), name=name, datatype=datatype, value=value)


# =====================================================================
# MACHINE 1: STAMPING PRESS
# Specialized parameters: Hydraulic pressure, Die temp, Tonnage, etc.
# =====================================================================
def create_stamping_press(device_id: str = "Machine01_Stamping") -> tuple[Device, dict]:
    state = {
        "status": 1,  # 1: Running, 0: Idle/Stopped
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
    # Randomly simulate running / idle state
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


# =====================================================================
# MACHINE 2: CNC MILLING MACHINE
# Specialized parameters: Spindle RPM, Feed Rate, Tool Wear, Coolant Flow
# =====================================================================
def create_cnc_machine(device_id: str = "Machine02_CNC") -> tuple[Device, dict]:
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


# =====================================================================
# MACHINE 3: PACKAGING & CONVEYOR
# Specialized parameters: Conveyor Speed, Carton Count, Sealing Temp, Jam
# =====================================================================
def create_packaging_line(device_id: str = "Machine03_Packaging") -> tuple[Device, dict]:
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
    # 5% chance of jam alarm, 10% chance stopped
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
    parser = argparse.ArgumentParser(description="Factory Line Sparkplug B Simulator")
    parser.add_argument("--broker", "-b", default=DEFAULT_BROKER_HOST, help="MQTT Broker host (default: localhost)")
    parser.add_argument("--port", "-p", type=int, default=DEFAULT_BROKER_PORT, help="MQTT Broker port (default: 1883)")
    parser.add_argument("--group", "-g", default=DEFAULT_GROUP_ID, help="Sparkplug Group ID (default: Plant1)")
    parser.add_argument("--node", "-n", default=DEFAULT_EDGE_NODE_ID, help="Sparkplug Edge Node ID (default: Line1)")
    args = parser.parse_args()

    print("=" * 70)
    print("  Sparkplug B Industrial Factory Simulator: Heterogeneous Machines")
    print("=" * 70)
    print(f"Group ID:      {args.group}")
    print(f"Edge Node ID:  {args.node}")
    print(f"Broker:        {args.broker}:{args.port}")
    print("Machines:")
    print("  1. Machine01_Stamping  -> Pressure, Die Temp, Tonnage, Stroke Count, Lube")
    print("  2. Machine02_CNC       -> Spindle RPM, Feed Rate, Tool Wear, Coolant, X/Y")
    print("  3. Machine03_Packaging -> Conveyor Speed, Cartons, Sealing Temp, Glue, Jam")
    print("-" * 70)

    # Edge Node Metrics (plant level health)
    node_metrics = [
        m("CPU_Load", DataType.FLOAT, 14.2),
        m("Line_Status", DataType.STRING, "NORMAL_OPERATION"),
    ]
    edge_node = EdgeNode(group_id=args.group, edge_node_id=args.node, metrics=node_metrics)

    # Instantiate the 3 machines with distinct schemas
    dev1, state1 = create_stamping_press("Machine01_Stamping")
    dev2, state2 = create_cnc_machine("Machine02_CNC")
    dev3, state3 = create_packaging_line("Machine03_Packaging")

    # Register each device (each announces its unique metric schema in DBIRTH)
    edge_node.register(dev1)
    edge_node.register(dev2)
    edge_node.register(dev3)
    print("Registered 3 distinct devices with customized parameters.")

    # Connect to Broker
    print(f"\nConnecting to broker at {args.broker}:{args.port}...")
    edge_node.connect(host=args.broker, port=args.port)
    time.sleep(1.5)  # Allow NBIRTH / DBIRTH handshake
    print("Connected! DBIRTH packets sent. Ignition will build custom tag trees for each.")
    print("Streaming live telemetry every 2 seconds. Press Ctrl+C to stop.\n")

    try:
        iteration = 1
        while True:
            # 1. Update Stamping Press
            m1 = update_stamping_press(state1)
            edge_node.update_device("Machine01_Stamping", m1)

            # 2. Update CNC Machine
            m2 = update_cnc_machine(state2)
            edge_node.update_device("Machine02_CNC", m2)

            # 3. Update Packaging Line
            m3 = update_packaging_line(state3)
            edge_node.update_device("Machine03_Packaging", m3)

            # Print telemetry summary
            print(f"[{time.strftime('%H:%M:%S')}] Cycle #{iteration}:")
            print(f"  • Stamping : Status={state1['status']} | Bar={state1['hydraulic_pressure']} | Temp={state1['die_temp']}°C | Strokes={state1['stroke_count']}")
            print(f"  • CNC      : Status={state2['status']} | RPM={state2['spindle_rpm']} | Wear={state2['tool_wear_pct']}% | Coolant={state2['coolant_flow_l_min']}L/min")
            print(f"  • Packaging: Status={state3['status']} | Speed={state3['conveyor_speed']}m/s | Cartons={state3['carton_count']} | Jam={state3['jam_alarm']}")

            iteration += 1
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopping factory simulation...")
        edge_node.disconnect()
        print("Disconnected gracefully (sent DDEATH/NDEATH certificates).")


if __name__ == "__main__":
    main()
