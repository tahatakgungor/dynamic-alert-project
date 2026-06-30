from dataclasses import dataclass


@dataclass(slots=True)
class FingerprintResult:
    protocol_name: str
    confidence: float
    details: str


class ProtocolAdapter:
    name = "unknown"

    def matches(self, open_ports: set[int]) -> bool:
        raise NotImplementedError

    def fingerprint(self, ip_address: str, open_ports: set[int]) -> FingerprintResult:
        raise NotImplementedError

    def sample_telemetry(self) -> list[dict]:
        return []
