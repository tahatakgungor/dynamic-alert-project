from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert.config import Settings
from dynamic_alert.database import Base
from dynamic_alert.models import Device, SemanticHypothesis, TelemetryRecord
from dynamic_alert.services.semantic_intelligence import SemanticIntelligenceService


def test_semantic_intelligence_learns_temperature_hypothesis() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        device = Device(ip_address="192.168.1.10", hostname="plc", vendor="Generic", status="online")
        db.add(device)
        db.commit()
        db.refresh(device)

        telemetry = TelemetryRecord(
            device_id=device.id,
            metric_key="temp_sensor_raw",
            value=63.5,
            unit=None,
            source_protocol="modbus_tcp",
        )
        db.add(telemetry)
        db.commit()
        db.refresh(telemetry)

        service = SemanticIntelligenceService(db, Settings())
        hypothesis = service.learn_from_telemetry(telemetry)

        assert hypothesis is not None
        assert hypothesis.predicted_metric_key == "temperature_c"
        assert hypothesis.learning_state == "learning"
        assert db.query(SemanticHypothesis).count() == 1
