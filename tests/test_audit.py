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
        assert db.query(AuditLog).count() == 1
