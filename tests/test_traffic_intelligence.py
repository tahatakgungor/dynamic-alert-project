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


def test_plaintext_topic_value_payload_creates_mqtt_like_candidate() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        cluster = FlowCluster(
            cluster_key="tcp:10.0.0.11:10.0.0.21:18830",
            protocol_hint="unknown",
            source_ip="10.0.0.11",
            destination_ip="10.0.0.21",
            destination_port=18830,
            transport="tcp",
            sample_count=2,
            last_payload_sample="factory/line1/temp 42.5",
        )
        db.add(cluster)
        db.commit()
        db.refresh(cluster)

        service = TrafficIntelligenceService(db)
        candidate = service.refresh_candidates_for_cluster(cluster)
        db.commit()

        assert candidate is not None
        assert candidate.candidate_label == "possible_mqtt_like_plaintext"
        assert "topic_value_plaintext" in candidate.evidence


def test_port_102_cluster_maps_to_possible_s7comm_flow() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        cluster = FlowCluster(
            cluster_key="tcp:10.0.0.12:10.0.0.22:102",
            protocol_hint="unknown",
            source_ip="10.0.0.12",
            destination_ip="10.0.0.22",
            destination_port=102,
            transport="tcp",
            sample_count=6,
            last_payload_sample="0300001611e00000",
        )
        db.add(cluster)
        db.commit()
        db.refresh(cluster)

        service = TrafficIntelligenceService(db)
        candidate = service.refresh_candidates_for_cluster(cluster)
        db.commit()

        assert candidate is not None
        assert candidate.candidate_label == "possible_s7comm_flow"
        assert candidate.confidence == 0.68


def test_operator_action_locks_candidate_status_against_refresh() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        cluster = FlowCluster(
            cluster_key="tcp:10.0.0.13:10.0.0.23:44818",
            protocol_hint="unknown",
            source_ip="10.0.0.13",
            destination_ip="10.0.0.23",
            destination_port=44818,
            transport="tcp",
            sample_count=2,
            last_payload_sample="deadbeef",
        )
        db.add(cluster)
        db.commit()
        db.refresh(cluster)

        service = TrafficIntelligenceService(db)
        candidate = service.refresh_candidates_for_cluster(cluster)
        db.commit()
        assert candidate is not None

        updated = service.apply_candidate_action(candidate_id=candidate.id, action="dismiss", notes="known benign flow")
        assert updated.status == "dismissed"
        assert updated.confidence == 0.0

        cluster.sample_count = 12
        db.add(cluster)
        db.commit()
        db.refresh(cluster)

        refreshed = service.refresh_candidates_for_cluster(cluster)
        db.commit()

        assert refreshed is not None
        assert refreshed.status == "dismissed"
        assert refreshed.candidate_label == candidate.candidate_label
