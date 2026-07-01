from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert.database import Base
from dynamic_alert.models import AuditLog, FlowCluster, UnknownProtocolCandidate
from dynamic_alert.services.audit import AuditLogService
from dynamic_alert.services.traffic_intelligence import TrafficIntelligenceService


def test_unknown_candidate_confirm_action_records_audit() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        cluster = FlowCluster(
            cluster_key="tcp:10.0.0.20:10.0.0.30:20000",
            protocol_hint="unknown",
            source_ip="10.0.0.20",
            destination_ip="10.0.0.30",
            destination_port=20000,
            transport="tcp",
            sample_count=4,
            last_payload_sample="a1b2c3d4",
        )
        db.add(cluster)
        db.commit()
        db.refresh(cluster)

        service = TrafficIntelligenceService(db)
        candidate = service.refresh_candidates_for_cluster(cluster)
        db.commit()
        assert candidate is not None

        updated = service.apply_candidate_action(
            candidate_id=candidate.id,
            action="confirm",
            candidate_label="confirmed_vendor_specific_flow",
            notes="validated in maintenance window",
        )
        AuditLogService(db).record(
            actor="operator",
            action="unknown-candidate.confirm",
            target=f"candidate:{updated.id}",
            details=updated.candidate_label,
        )

        saved = db.query(UnknownProtocolCandidate).one()
        audit = db.query(AuditLog).filter(AuditLog.action == "unknown-candidate.confirm").one()

        assert saved.status == "confirmed"
        assert saved.candidate_label == "confirmed_vendor_specific_flow"
        assert saved.confidence == 1.0
        assert "operator_note=validated in maintenance window" in saved.evidence
        assert audit.target == f"candidate:{saved.id}"
