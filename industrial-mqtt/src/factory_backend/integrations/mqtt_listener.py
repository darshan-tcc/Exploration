"""Ignition MQTT Ingestion Subscriber.

Subscribes directly to Ignition SCADA's MQTT Distributor broker.
Ingests machine telemetry and feeds into the Common Ingestion Pipeline.
"""

import asyncio
import json
import logging
import paho.mqtt.client as mqtt
from factory_backend.core.config import settings
from factory_backend.pipeline.processor import pipeline

logger = logging.getLogger("factory_backend.integrations.mqtt")


class MqttListener:
    """Async-compatible MQTT Subscriber listening to Ignition MQTT telemetry."""

    def __init__(self):
        self.client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID, clean_session=True)
        if settings.MQTT_USERNAME:
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self._loop: asyncio.AbstractEventLoop | None = None
        self._connected = False

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info(f"Connected to Ignition MQTT Broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
            client.subscribe(settings.MQTT_TOPIC_TELEMETRY, qos=1)
            logger.info(f"Subscribed to topic: {settings.MQTT_TOPIC_TELEMETRY}")
        else:
            logger.error(f"Ignition MQTT connection refused with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            logger.warning("Unexpected disconnection from Ignition MQTT Broker. Auto-reconnecting...")

    def _on_message(self, client, userdata, msg):
        try:
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    pipeline.process(raw_data=data, source_type="ignition_mqtt"),
                    self._loop,
                )
        except Exception as ex:
            logger.warning(f"Failed to process message on {msg.topic}: {ex}")

    def start(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        try:
            self.client.connect_async(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60)
            self.client.loop_start()
            logger.info("Ignition MQTT Listener client loop started.")
        except Exception as ex:
            logger.error(f"Could not connect to Ignition MQTT broker: {ex}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Ignition MQTT Listener stopped.")


mqtt_listener = MqttListener()
