from __future__ import annotations

import json
from pathlib import Path


SNMP_OID_KEYS = ("snmp_oid_sysdescr", "snmp_oid_sysname", "snmp_oid_uptime")


class SnmpOidRepository:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def resolve(self, oid_set: str | None = None) -> dict[str, str]:
        if not self.path.exists():
            return {}
        payload = json.loads(self.path.read_text())
        return self._resolve_oids(payload, oid_set=oid_set)

    def oid_sets(self) -> list[str]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text())
        if isinstance(payload, dict) and isinstance(payload.get("oid_sets"), dict):
            return list(payload["oid_sets"].keys())
        return []

    @staticmethod
    def _resolve_oids(payload: object, *, oid_set: str | None) -> dict[str, str]:
        if isinstance(payload, dict) and any(key in payload for key in SNMP_OID_KEYS):
            return {
                key: str(payload[key])
                for key in SNMP_OID_KEYS
                if key in payload and str(payload[key]).strip()
            }
        if not isinstance(payload, dict):
            return {}

        oid_sets = payload.get("oid_sets")
        if not isinstance(oid_sets, dict):
            return {}

        selected_set = oid_set or payload.get("default_set")
        if not selected_set:
            return {}

        selected = oid_sets.get(selected_set, {})
        if not isinstance(selected, dict):
            return {}
        return {
            key: str(selected[key])
            for key in SNMP_OID_KEYS
            if key in selected and str(selected[key]).strip()
        }
