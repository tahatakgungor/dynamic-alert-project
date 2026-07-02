from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert.config import Settings
from dynamic_alert.database import Base
from dynamic_alert.models import AlertEvent, SemanticHypothesis, Site, TelemetryRecord, Workspace
from dynamic_alert.services.demo_scenarios import run_demo_scenario


def test_modbus_catalog_demo_scenario_reaches_alert_flow() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        workspace = Workspace(name="HQ", slug="hq")
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        db.add(Site(workspace_id=workspace.id, name="HQ Plant", code="HQ-PLANT", timezone="UTC"))
        db.commit()

        result = run_demo_scenario(db, Settings(), "modbus_catalog_alert")

        assert result["scenario_key"] == "modbus_catalog_alert"
        telemetry = db.query(TelemetryRecord).order_by(TelemetryRecord.id.desc()).first()
        hypothesis = db.query(SemanticHypothesis).order_by(SemanticHypothesis.id.desc()).first()
        alert = db.query(AlertEvent).order_by(AlertEvent.id.desc()).first()

        assert telemetry is not None
        assert telemetry.source_protocol == "modbus_tcp"
        assert hypothesis is not None
        assert result["latest_semantic"]["predicted_metric_key"] == "temperature_c"
        assert alert is not None
        assert "temperature_c" in alert.message
        assert result["latest_telemetry"]["metric_key"] == "temperature_c"
