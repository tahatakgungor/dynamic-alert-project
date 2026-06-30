from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert.database import Base
from dynamic_alert.models import FlowCluster, UnknownProtocolCandidate
from dynamic_alert.services.traffic_intelligence import TrafficIntelligenceService


def test_unknown_cluster_creates_candidate() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        cluster = FlowCluster(
            cluster_key="tcp:10.0.0.10:10.0.0.20:20000",
            protocol_hint="unknown",
            source_ip="10.0.0.10",
            destination_ip="10.0.0.20",
            destination_port=20000,
            transport="tcp",
            sample_count=3,
            last_payload_sample="a1b2c3d4",
        )
        db.add(cluster)
        db.commit()
        db.refresh(cluster)

        service = TrafficIntelligenceService(db)
        candidate = service.refresh_candidates_for_cluster(cluster)
        db.commit()

        assert candidate is not None
        assert candidate.candidate_label == "industrial_unknown_high_priority"
        assert db.query(UnknownProtocolCandidate).count() == 1
