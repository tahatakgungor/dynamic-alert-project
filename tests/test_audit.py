from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert.database import Base
from dynamic_alert.models import AuditLog
from dynamic_alert.services.audit import AuditLogService


def test_audit_log_service_records_entries() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        AuditLogService(db).record(actor="tester", action="scan.run", target="network", details="ok")
        item = db.query(AuditLog).one()
        assert item.actor == "tester"
        assert item.action == "scan.run"
        assert item.status == "ok"


def test_audit_log_service_redacts_sensitive_details() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        AuditLogService(db).record(
            actor="tester",
            action="config.update",
            target="settings",
            details="token=123456789:ABCDEFGHIJKLMNOPQRSTUV api_key=secret-value",
        )
        item = db.query(AuditLog).one()
        assert "token=[redacted]" in (item.details or "")
        assert "api_key=[redacted]" in (item.details or "")
        assert "secret-value" not in (item.details or "")
