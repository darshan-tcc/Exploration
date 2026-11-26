"""Ignition MQTT Subscriber Client.

Subscribes directly to Ignition SCADA's MQTT Distributor broker (port 1883).
Listens to live telemetry from the factory machines and prints received parameters in real-time.

Run with:
    python subscriber.py
"""

import argparse
import os
import sys
import time
import paho.mqtt.client as mqtt

# ==============================================================================
# 1. MQTT CONNECTION CONFIGURATION
# ==============================================================================
DEFAULT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
DEFAULT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
DEFAULT_USERNAME = os.getenv("MQTT_USERNAME", "admin")
DEFAULT_PASSWORD = os.getenv("MQTT_PASSWORD", "changeme")

# Sparkplug B Telemetry Topic: spBv1.0/<GROUP>/DDATA/<EDGE_NODE>/<DEVICE>
# We subscribe to '#' to capture all telemetry, births, and deaths across all machines
TOPIC_SPARKPLUG_ALL = "spBv1.0/#"


def on_connect(client, userdata, flags, rc):
    """Callback triggered when subscriber connects to Ignition MQTT Distributor."""
    if rc == 0:
        print("[SUBSCRIBER] Connected successfully to Ignition MQTT Broker!")
        # Subscribe to all Sparkplug B telemetry topics with QoS 1
        client.subscribe(TOPIC_SPARKPLUG_ALL, qos=1)
        print(f"[SUBSCRIBER] Subscribed to topic pattern: {TOPIC_SPARKPLUG_ALL}")
        print("[SUBSCRIBER] Waiting for live machine data... (Press Ctrl+C to stop)\n")
    else:
        print(f"[SUBSCRIBER] Connection failed with error code: {rc}")


def on_message(client, userdata, msg):
    """Callback triggered whenever a machine publishes data."""
    topic = msg.topic
    payload_len = len(msg.payload)
    timestamp_str = time.strftime("%H:%M:%S")

    # Topic format: spBv1.0/Plant1/DDATA/Line1/Machine01_Stamping
    topic_parts = topic.split("/")
    msg_type = topic_parts[2] if len(topic_parts) > 2 else "UNKNOWN"
    device_id = topic_parts[4] if len(topic_parts) > 4 else "EdgeNode"

    if msg_type == "DDATA":
        print(f"[{timestamp_str}] [DDATA RECEIVED] Machine: {device_id:20} | Bytes: {payload_len:4} | Topic: {topic}")
    elif msg_type == "DBIRTH":
        print(f"[{timestamp_str}] [DBIRTH DISCOVERY] Machine Registered: {device_id} (New Tag Tree Created in Ignition)")
    elif msg_type == "NBIRTH":
        print(f"[{timestamp_str}] [NBIRTH DISCOVERY] Line Online: {topic_parts[3] if len(topic_parts) > 3 else ''}")
    elif msg_type == "DDEATH":
        print(f"[{timestamp_str}] [DDEATH WARNING] Machine Offline: {device_id}")
    else:
        print(f"[{timestamp_str}] [{msg_type}] Topic: {topic} ({payload_len} bytes)")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("[SUBSCRIBER] Unexpected disconnection from Ignition. Reconnecting...")


def main():
    parser = argparse.ArgumentParser(description="Ignition MQTT Sparkplug B Subscriber")
    parser.add_argument("--broker", "-b", default=DEFAULT_BROKER_HOST, help="MQTT Broker host (default: localhost)")
    parser.add_argument("--port", "-p", type=int, default=DEFAULT_BROKER_PORT, help="MQTT Broker port (default: 1883)")
    parser.add_argument("--user", "-u", default=DEFAULT_USERNAME, help="MQTT username (default: admin)")
    parser.add_argument("--password", "-P", default=DEFAULT_PASSWORD, help="MQTT password (default: changeme)")
    args = parser.parse_args()

    print("=" * 70)
    print("  Ignition MQTT Subscriber Client (Telemetry Receiver)")
    print("=" * 70)
    print(f"Target Broker: tcp://{args.broker}:{args.port}")
    print(f"Listening on:  {TOPIC_SPARKPLUG_ALL}")
    print("-" * 70)

    client = mqtt.Client(client_id="ignition_telemetry_subscriber", clean_session=True)
    if args.user:
        client.username_pw_set(args.user, args.password)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        client.connect(args.broker, args.port, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[SUBSCRIBER] Stopping subscriber...")
        client.disconnect()
        print("[SUBSCRIBER] Disconnected.")
    except Exception as ex:
        print(f"\n[ERROR] Could not connect to Ignition: {ex}")
        print("Ensure Ignition Gateway is running at http://localhost:8088 with MQTT Distributor.")


if __name__ == "__main__":
    main()
