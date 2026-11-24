import json
import random
import time

import paho.mqtt.client as mqtt
# pyrefly: ignore[missing-import]
from paho.mqtt.enums import CallbackAPIVersion

BROKER = "localhost"
PORT = 1883

TOPIC = "plant/line1/machine01/telemetry"

machine_id = "MACHINE-01"
production_count = 0


def generate_telemetry():
    global production_count

    running = random.choice([True, True, True, False])

    if running:
        production_count += random.randint(1, 3)

    data = {
        "machine_id": machine_id,
        "temperature": round(random.uniform(25, 80), 2),
        "pressure": round(random.uniform(4, 8), 2),
        "motor_rpm": random.randint(1000, 1800) if running else 0,
        "running": running,
        "production_count": production_count,
        "timestamp": time.time(),
    }

    return data


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT broker: {reason_code}")


client = mqtt.Client(CallbackAPIVersion.VERSION2)

client.on_connect = on_connect

client.connect(BROKER, PORT, 60,)

client.loop_start()

try:
    while True:
        telemetry = generate_telemetry()

        payload = json.dumps(telemetry)

        client.publish(TOPIC, payload, qos=0)

        print(f"Published: {payload}")

        time.sleep(2)

except KeyboardInterrupt:
    print("\nMachine simulator stopped.")

    client.disconnect()
    client.loop_stop()