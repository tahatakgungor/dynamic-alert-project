from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dynamic_alert.services.discovery import DiscoveredDevice


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

    def collect_telemetry(self, device: "DiscoveredDevice") -> list[dict]:
        return []
