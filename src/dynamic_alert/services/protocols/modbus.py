from dynamic_alert.services.protocols.base import FingerprintResult, ProtocolAdapter


class ModbusAdapter(ProtocolAdapter):
    name = "modbus_tcp"

    def matches(self, open_ports: set[int]) -> bool:
        return 502 in open_ports

    def fingerprint(self, ip_address: str, open_ports: set[int]) -> FingerprintResult:
        return FingerprintResult(
            protocol_name=self.name,
            confidence=0.92,
            details=f"{ip_address} cihazinda 502/tcp acik. Modbus/TCP yuksek olasilik.",
        )

    def sample_telemetry(self) -> list[dict]:
        return [
            {"metric_key": "temperature_c", "value": 71.3, "unit": "C", "source_protocol": self.name},
            {"metric_key": "pressure_bar", "value": 3.8, "unit": "bar", "source_protocol": self.name},
        ]
