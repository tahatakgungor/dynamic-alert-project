from __future__ import annotations

from dynamic_alert.config import Settings
from dynamic_alert.services.discovery import DiscoveredDevice
from dynamic_alert.services.protocols.base import FingerprintResult, ProtocolAdapter
from dynamic_alert.services.protocols.snmp_oids import SnmpOidRepository


class SnmpAdapter(ProtocolAdapter):
    name = "snmp"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.oid_repository = SnmpOidRepository(settings.snmp_oid_sets_path)

    def matches(self, open_ports: set[int]) -> bool:
        return self.settings.snmp_port in open_ports

    def fingerprint(self, ip_address: str, open_ports: set[int]) -> FingerprintResult:
        return FingerprintResult(
            protocol_name=self.name,
            confidence=0.84,
            details=f"{ip_address} cihazinda {self.settings.snmp_port}/udp veya yonetim yuzeyi acik olabilir.",
        )

    def collect_telemetry(self, device: DiscoveredDevice) -> list[dict]:
        try:
            from pysnmp.hlapi.asyncio import (
                CommunityData,
                ObjectIdentity,
                ObjectType,
                SnmpEngine,
                UdpTransportTarget,
                get_cmd,
            )
        except ImportError:
            return []

        import asyncio

        async def run_probe() -> list[dict]:
            target = await UdpTransportTarget.create(
                (device.ip_address, self.settings.snmp_port),
                timeout=self.settings.snmp_timeout_seconds,
                retries=0,
            )
            engine = SnmpEngine()
            telemetry: list[dict] = []
            oid_config = self.oid_repository.resolve(self.settings.snmp_oid_set) if self.settings.snmp_oid_set else {}
            for oid, metric_key in (
                (oid_config.get("snmp_oid_sysdescr", self.settings.snmp_oid_sysdescr), "snmp_sysdescr"),
                (oid_config.get("snmp_oid_sysname", self.settings.snmp_oid_sysname), "snmp_sysname"),
                (oid_config.get("snmp_oid_uptime", self.settings.snmp_oid_uptime), "snmp_uptime_ticks"),
            ):
                try:
                    error_indication, error_status, _, var_binds = await get_cmd(
                        engine,
                        CommunityData(self.settings.snmp_community),
                        target,
                        ObjectType(ObjectIdentity(oid)),
                    )
                except Exception:
                    continue

                if error_indication or error_status:
                    continue
                for _, value in var_binds:
                    rendered = str(value)
                    numeric_value = self._coerce_numeric(rendered)
                    telemetry.append(
                        {
                            "metric_key": metric_key,
                            "value": numeric_value,
                            "unit": None,
                            "source_protocol": self.name,
                            "metadata_text": rendered,
                        }
                    )
            engine.transport_dispatcher.close_dispatcher()
            return telemetry

        try:
            return asyncio.run(run_probe())
        except RuntimeError:
            return []

    @staticmethod
    def _coerce_numeric(value: str) -> float:
        try:
            return float(value)
        except ValueError:
            return float(len(value))
