from sqlalchemy.orm import Session

from dynamic_alert.models import Device, ProtocolFingerprint, TelemetryRecord
from dynamic_alert.services.discovery import NetworkDiscoveryService
from dynamic_alert.services.protocols.registry import ProtocolRegistry
from dynamic_alert.services.rule_engine import RuleEngine


class IngestionCoordinator:
    def __init__(
        self,
        db: Session,
        discovery: NetworkDiscoveryService,
        protocol_registry: ProtocolRegistry,
        rule_engine: RuleEngine,
    ) -> None:
        self.db = db
        self.discovery = discovery
        self.protocol_registry = protocol_registry
        self.rule_engine = rule_engine

    def run_cycle(self) -> dict[str, int]:
        discovered = self.discovery.scan()
        telemetry_count = 0
        device_count = 0

        for item in discovered:
            device = self.db.query(Device).filter(Device.ip_address == item.ip_address).one_or_none()
            if device is None:
                device = Device(
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

                for sample in adapter.sample_telemetry():
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
                    self.rule_engine.evaluate(telemetry)
                    telemetry_count += 1
                break

        return {"new_devices": device_count, "telemetry_records": telemetry_count}
