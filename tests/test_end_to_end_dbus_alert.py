from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert.config import Settings
from dynamic_alert.database import Base
from dynamic_alert.models import AlertEvent, AlertRule, AuditLog, Device, SemanticHypothesis, Site, TelemetryRecord, Workspace
from dynamic_alert.services.discovery import DiscoveredDevice, NetworkDiscoveryService
from dynamic_alert.services.ingestion import IngestionCoordinator
from dynamic_alert.services.protocols.dbus import DBusAdapter
from dynamic_alert.services.protocols.registry import ProtocolRegistry
from dynamic_alert.services.rule_engine import RuleEngine
from dynamic_alert.services.semantic_intelligence import SemanticIntelligenceService


class CapturingNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, message: str) -> bool:
        self.messages.append(message)
        return True


def test_dbus_temperature_flow_reaches_semantic_alert_and_notifier() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        workspace = Workspace(name="HQ", slug="hq")
        db.add(workspace)
        db.commit()
        db.refresh(workspace)

        site = Site(workspace_id=workspace.id, name="HQ Plant", code="HQ-PLANT", timezone="UTC")
        db.add(site)
        db.add(
            AlertRule(
                name="semantic_temperature_high",
                metric_key="temperature_c",
                operator=">=",
                threshold=70.0,
                severity="critical",
                enabled=True,
                notification_channel="telegram",
            )
        )
        db.commit()

        notifier = CapturingNotifier()
        coordinator = IngestionCoordinator(
            db=db,
            discovery=NetworkDiscoveryService([]),
            protocol_registry=ProtocolRegistry([DBusAdapter()]),
            rule_engine=RuleEngine(db, notifier),  # type: ignore[arg-type]
            semantic_intelligence=SemanticIntelligenceService(db, Settings()),
        )

        result = coordinator.ingest_device(
            DiscoveredDevice(
                site_code="HQ-PLANT",
                ip_address="192.168.1.250",
                hostname="press-line-gateway",
                vendor="Linux Edge Gateway",
                open_ports={22, 80},
            )
        )

        assert result == {"new_devices": 1, "telemetry_records": 1}
        assert db.query(Device).count() == 1
        telemetry = db.query(TelemetryRecord).one()
        hypothesis = db.query(SemanticHypothesis).one()
        event = db.query(AlertEvent).one()
        audit_item = db.query(AuditLog).filter(AuditLog.action == "alert.triggered").one()

        assert telemetry.metric_key == "dbus_sensor_temperature_raw"
        assert hypothesis.predicted_metric_key == "temperature_c"
        assert hypothesis.predicted_unit == "C"
        assert event.delivered is True
        assert "semantic_metric=temperature_c" in event.message
        assert audit_item.target == "semantic_temperature_high"
        assert audit_item.status == "delivered"
        assert notifier.messages
