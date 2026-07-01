from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from dynamic_alert.models import Device, ProtocolFingerprint, Site, TelemetryRecord
from dynamic_alert.services.semantic_intelligence import SemanticIntelligenceService
from dynamic_alert.services.discovery import NetworkDiscoveryService
from dynamic_alert.services.protocols.registry import ProtocolRegistry
from dynamic_alert.services.rule_engine import RuleEngine

if TYPE_CHECKING:
    from dynamic_alert.services.discovery import DiscoveredDevice


class IngestionCoordinator:
    def __init__(
        self,
        db: Session,
        discovery: NetworkDiscoveryService,
        protocol_registry: ProtocolRegistry,
        rule_engine: RuleEngine,
        semantic_intelligence: SemanticIntelligenceService,
    ) -> None:
        self.db = db
        self.discovery = discovery
        self.protocol_registry = protocol_registry
        self.rule_engine = rule_engine
        self.semantic_intelligence = semantic_intelligence

    def run_cycle(self) -> dict[str, int]:
        discovered = self.discovery.scan()
        telemetry_count = 0
        device_count = 0

        for item in discovered:
            result = self.ingest_device(item)
            telemetry_count += result["telemetry_records"]
            device_count += result["new_devices"]

        return {"new_devices": device_count, "telemetry_records": telemetry_count}

    def ingest_device(self, item: "DiscoveredDevice") -> dict[str, int]:
        site = self.db.query(Site).filter(Site.code == item.site_code).one_or_none()
        device = self.db.query(Device).filter(Device.ip_address == item.ip_address).one_or_none()
        device_count = 0
        telemetry_count = 0

        if device is None:
            device = Device(
                site_id=site.id if site else None,
                ip_address=item.ip_address,
                hostname=item.hostname,
                vendor=item.vendor,
                status="online",
            )
            self.db.add(device)
            self.db.commit()
            self.db.refresh(device)
            device_count += 1

        for adapter in self.protocol_registry.all():
            if not adapter.matches(item.open_ports):
                continue

            fingerprint = adapter.fingerprint(item.ip_address, item.open_ports)
            self.db.add(
                ProtocolFingerprint(
                    device_id=device.id,
                    protocol_name=fingerprint.protocol_name,
                    confidence=fingerprint.confidence,
                    details=fingerprint.details,
                )
            )
            self.db.commit()

            for sample in adapter.collect_telemetry(item):
                telemetry = TelemetryRecord(
                    device_id=device.id,
                    metric_key=sample["metric_key"],
                    value=sample["value"],
                    unit=sample.get("unit"),
                    source_protocol=sample["source_protocol"],
                )
                self.db.add(telemetry)
                self.db.commit()
                self.db.refresh(telemetry)
                hypothesis = self.semantic_intelligence.learn_from_telemetry(telemetry)
                self.rule_engine.evaluate(
                    telemetry,
                    semantic_metric_key=hypothesis.predicted_metric_key if hypothesis is not None else None,
                )
                telemetry_count += 1
            break

        return {"new_devices": device_count, "telemetry_records": telemetry_count}
