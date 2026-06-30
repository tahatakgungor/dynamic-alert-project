from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert.config import Settings
from dynamic_alert.database import Base
from dynamic_alert.models import Device, SemanticMap, TelemetryRecord
from dynamic_alert.services.semantic_intelligence import SemanticIntelligenceService
from dynamic_alert.services.semantic_map import SemanticMapService


def test_operator_semantic_map_overrides_heuristic() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        device = Device(ip_address="192.168.1.30", hostname="gateway", vendor="Industrial IPC", status="online")
        db.add(device)
        db.commit()
        db.refresh(device)

        SemanticMapService(db).upsert_operator_map(
            scope="device",
            device_id=device.id,
            vendor=device.vendor,
            protocol_name="mqtt",
            source_key="mqtt_factory_line1_temp",
            metric_key="line_temperature_c",
            unit="C",
        )

        telemetry = TelemetryRecord(
            device_id=device.id,
            metric_key="mqtt_factory_line1_temp",
            value=44.0,
            unit=None,
            source_protocol="mqtt",
        )
        db.add(telemetry)
        db.commit()
        db.refresh(telemetry)

        hypothesis = SemanticIntelligenceService(db, Settings()).learn_from_telemetry(telemetry)

        assert hypothesis is not None
        assert hypothesis.predicted_metric_key == "line_temperature_c"
        assert hypothesis.learning_state == "confirmed"
        assert db.query(SemanticMap).count() == 1
