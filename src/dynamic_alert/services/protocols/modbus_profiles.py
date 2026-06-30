from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from dynamic_alert.services.discovery import DiscoveredDevice


@dataclass(slots=True)
class ModbusRegisterProfile:
    name: str
    metric_key: str
    register_type: str
    address: int
    count: int
    unit_id: int
    unit: str | None = None
    scale: float = 1.0
    offset: float = 0.0
    signed: bool = False
    vendor: str | None = None
    hostname_contains: str | None = None
    ip_address: str | None = None

    def matches(self, device: DiscoveredDevice) -> bool:
        if self.vendor and self.vendor.lower() != (device.vendor or "").lower():
            return False
        if self.hostname_contains and self.hostname_contains.lower() not in (device.hostname or "").lower():
            return False
        if self.ip_address and self.ip_address != device.ip_address:
            return False
        return True


class ModbusProfileRepository:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def load(self) -> list[ModbusRegisterProfile]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text())
        return [ModbusRegisterProfile(**item) for item in payload]

    def match(self, device: DiscoveredDevice) -> list[ModbusRegisterProfile]:
        return [profile for profile in self.load() if profile.matches(device)]
