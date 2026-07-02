from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert.config import Settings
from dynamic_alert.database import Base
from dynamic_alert.models import Device, TelemetryRecord
from dynamic_alert.services.semantic_intelligence import SemanticIntelligenceService


def test_modbus_pressure_metric_prefers_pressure_over_temperature() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        device = Device(ip_address="10.20.30.20", hostname="thermal-loop-01", vendor="Generic PLC", status="online")
        db.add(device)
        db.commit()
        db.refresh(device)

        telemetry = TelemetryRecord(
            device_id=device.id,
            metric_key="pressure_bar",
            value=5.2,
            unit="bar",
            source_protocol="modbus_tcp",
        )
        db.add(telemetry)
        db.commit()
        db.refresh(telemetry)

        hypothesis = SemanticIntelligenceService(db, Settings()).learn_from_telemetry(telemetry)

        assert hypothesis is not None
        assert hypothesis.predicted_metric_key == "pressure_bar"
        assert hypothesis.predicted_unit == "bar"
