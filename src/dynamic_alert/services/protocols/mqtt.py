from __future__ import annotations

import time

from dynamic_alert.config import Settings
from dynamic_alert.services.discovery import DiscoveredDevice
from dynamic_alert.services.protocols.base import FingerprintResult, ProtocolAdapter


class MqttAdapter(ProtocolAdapter):
    name = "mqtt"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def matches(self, open_ports: set[int]) -> bool:
        return 1883 in open_ports

    def fingerprint(self, ip_address: str, open_ports: set[int]) -> FingerprintResult:
        return FingerprintResult(
            protocol_name=self.name,
            confidence=0.83,
            details=f"{ip_address} cihazinda 1883/tcp acik. MQTT broker veya gateway olabilir.",
        )

    def collect_telemetry(self, device: DiscoveredDevice) -> list[dict]:
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            return []

        messages: list[dict] = []
        callback_api = getattr(getattr(mqtt, "CallbackAPIVersion", None), "VERSION2", None)
        client = mqtt.Client(callback_api) if callback_api is not None else mqtt.Client()

        def on_message(_: mqtt.Client, __, message) -> None:
            payload_text = message.payload.decode("utf-8", errors="ignore").strip()
            numeric_value = self._extract_numeric(payload_text)
            messages.append(
                {
                    "metric_key": f"mqtt_{message.topic.replace('/', '_')}",
                    "value": numeric_value,
                    "unit": None,
                    "source_protocol": self.name,
                    "metadata_text": payload_text,
                }
            )

        client.on_message = on_message

        try:
            client.connect(device.ip_address, 1883, int(self.settings.mqtt_probe_timeout_seconds))
            for topic in self.settings.mqtt_probe_topics:
                client.subscribe(topic)
            client.loop_start()
            deadline = time.time() + self.settings.mqtt_probe_timeout_seconds
            while time.time() < deadline and len(messages) < self.settings.mqtt_probe_max_messages:
                time.sleep(0.1)
        except Exception:
            return []
        finally:
            try:
                client.loop_stop()
                client.disconnect()
            except Exception:
                pass

        return messages[: self.settings.mqtt_probe_max_messages]

    @staticmethod
    def _extract_numeric(payload_text: str) -> float:
        for chunk in payload_text.replace(",", " ").split():
            try:
                return float(chunk)
            except ValueError:
                continue
        return float(len(payload_text))
