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

    def load(self, profile_set: str | None = None) -> list[ModbusRegisterProfile]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text())
        raw_profiles = self._resolve_profile_items(payload, profile_set=profile_set)
        return [ModbusRegisterProfile(**item) for item in raw_profiles]

    def match(self, device: DiscoveredDevice, *, profile_set: str | None = None) -> list[ModbusRegisterProfile]:
        return [profile for profile in self.load(profile_set=profile_set) if profile.matches(device)]

    def profile_sets(self) -> list[str]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text())
        if isinstance(payload, dict) and isinstance(payload.get("profile_sets"), dict):
            return list(payload["profile_sets"].keys())
        return []

    @staticmethod
    def _resolve_profile_items(payload: object, *, profile_set: str | None) -> list[dict]:
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []

        profile_sets = payload.get("profile_sets")
        if not isinstance(profile_sets, dict):
            return []

        selected_set = profile_set or payload.get("default_set")
        if selected_set:
            items = profile_sets.get(selected_set, [])
            return items if isinstance(items, list) else []

        combined: list[dict] = []
        for items in profile_sets.values():
            if isinstance(items, list):
                combined.extend(items)
        return combined
