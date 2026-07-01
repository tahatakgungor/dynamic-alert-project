from __future__ import annotations

from dynamic_alert.services.discovery import DiscoveredDevice
from dynamic_alert.services.protocols.base import FingerprintResult, ProtocolAdapter


class DBusAdapter(ProtocolAdapter):
    name = "dbus_gateway"

    def matches(self, open_ports: set[int]) -> bool:
        return 22 in open_ports and 80 in open_ports

    def fingerprint(self, ip_address: str, open_ports: set[int]) -> FingerprintResult:
        return FingerprintResult(
            protocol_name=self.name,
            confidence=0.40,
            details=f"{ip_address} Linux tabanli bir gateway olabilir; D-Bus yerel entegrasyon icin aday.",
        )

    def collect_telemetry(self, device: DiscoveredDevice) -> list[dict]:
        temperature_value = self._derive_demo_temperature(device)
        return [
            {
                "metric_key": "dbus_sensor_temperature_raw",
                "value": temperature_value,
                "unit": "C",
                "source_protocol": self.name,
                "metadata_text": f"host={device.hostname or device.ip_address}",
            }
        ]

    @staticmethod
    def _derive_demo_temperature(device: DiscoveredDevice) -> float:
        basis = f"{device.hostname or ''}:{device.vendor or ''}:{device.ip_address}"
        if "press" in basis.lower():
            return 81.5
        return 74.0
