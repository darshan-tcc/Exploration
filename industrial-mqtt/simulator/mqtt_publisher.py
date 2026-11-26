"""MQTT Publisher Simulation.

Publishes heterogeneous machine telemetry in standard JSON format:
  - plant/Plant1/Line1/telemetry

Machines simulated:
  - M01 (Stamping Press)
  - M02 (CNC Milling Center)
  - M03 (Packaging & Conveyor)
"""

import datetime
import json
import random
import time
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "plant/Plant1/Line1/telemetry"


def main():
    client = mqtt.Client(client_id="machine_telemetry_publisher")
    print(f"Connecting to MQTT broker at {BROKER_HOST}:{BROKER_PORT}...")
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    print("Connected! Streaming telemetry to topic:", TOPIC)

    try:
        stroke_count = 1450
        carton_count = 920
        while True:
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

            # M01 - Stamping Press
            stroke_count += random.randint(1, 3)
            payload_m01 = {
                "machine_id": "M01",
                "status": 1 if random.random() > 0.1 else 0,
                "timestamp": now_iso,
                "parameters": {
                    "hydraulic_pressure": round(random.uniform(175.0, 195.0), 1),
                    "die_temp": round(random.uniform(60.0, 75.0), 1),
                    "tonnage": round(random.uniform(230.0, 255.0), 1),
                    "stroke_count": stroke_count,
                    "lubrication_level": round(random.uniform(80.0, 95.0), 1),
                },
            }
            client.publish(TOPIC, json.dumps(payload_m01), qos=1)

            # M02 - CNC
            payload_m02 = {
                "machine_id": "M02",
                "status": 1 if random.random() > 0.1 else 0,
                "timestamp": now_iso,
                "parameters": {
                    "spindle_rpm": random.randint(3400, 4200),
                    "feed_rate": round(random.uniform(1150.0, 1350.0), 1),
                    "tool_wear": round(random.uniform(12.0, 18.0), 2),
                    "coolant_flow": round(random.uniform(16.5, 20.0), 1),
                },
            }
            client.publish(TOPIC, json.dumps(payload_m02), qos=1)

            # M03 - Packaging
            carton_count += random.randint(1, 4)
            payload_m03 = {
                "machine_id": "M03",
                "status": 1 if random.random() > 0.1 else 0,
                "timestamp": now_iso,
                "parameters": {
                    "conveyor_speed": round(random.uniform(1.15, 1.40), 2),
                    "carton_count": carton_count,
                    "sealing_temp": round(random.uniform(142.0, 148.0), 1),
                    "jam_alarm": random.random() < 0.05,
                },
            }
            client.publish(TOPIC, json.dumps(payload_m03), qos=1)

            print(f"[{time.strftime('%H:%M:%S')}] Published telemetry for M01, M02, M03")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopping publisher...")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
