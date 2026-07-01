from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert.config import Settings
from dynamic_alert.database import Base
from dynamic_alert.models import EdgeNode, Site, Workspace
from dynamic_alert.schemas import EdgeJobCreate, EdgeJobResultRequest, EdgeNodeHeartbeatRequest
from dynamic_alert.services.edge_runtime import EdgeRuntimeService


def test_non_development_rejects_default_bootstrap_key() -> None:
    settings = Settings(env="production", bootstrap_api_key="change-me-before-production")
    try:
        settings.validate_security()
    except ValueError as exc:
        assert "bootstrap_api_key" in str(exc)
        return
    raise AssertionError("expected production bootstrap validation error")


def test_edge_job_schema_rejects_invalid_job_kind() -> None:
    try:
        EdgeJobCreate(edge_node_id=1, job_kind="rm-rf", payload=None)
    except ValueError as exc:
        assert "unsupported edge job kind" in str(exc)
        return
    raise AssertionError("expected edge job kind validation error")


def test_edge_job_schema_rejects_invalid_enabled_protocols() -> None:
    try:
        EdgeJobCreate(edge_node_id=1, job_kind="scan", payload={"enabled_protocols": ["ssh"]})
    except ValueError as exc:
        assert "unsupported protocol names" in str(exc)
        return
    raise AssertionError("expected enabled_protocols validation error")


def test_edge_job_schema_rejects_invalid_mqtt_topics_shape() -> None:
    try:
        EdgeJobCreate(edge_node_id=1, job_kind="scan", payload={"mqtt_probe_topics": "factory/#"})
    except ValueError as exc:
        assert "mqtt_probe_topics payload" in str(exc)
        return
    raise AssertionError("expected mqtt_probe_topics validation error")


def test_edge_job_schema_rejects_invalid_mqtt_topic_set_shape() -> None:
    try:
        EdgeJobCreate(edge_node_id=1, job_kind="scan", payload={"mqtt_topic_set": ["factory_default"]})
    except ValueError as exc:
        assert "mqtt_topic_set payload" in str(exc)
        return
    raise AssertionError("expected mqtt_topic_set validation error")


def test_edge_job_schema_rejects_invalid_modbus_profile_set_shape() -> None:
    try:
        EdgeJobCreate(edge_node_id=1, job_kind="scan", payload={"modbus_profile_set": ["generic_plc"]})
    except ValueError as exc:
        assert "modbus_profile_set payload" in str(exc)
        return
    raise AssertionError("expected modbus_profile_set validation error")


def test_edge_job_schema_rejects_invalid_snmp_oid_set_shape() -> None:
    try:
        EdgeJobCreate(edge_node_id=1, job_kind="scan", payload={"snmp_oid_set": ["standard_mib2"]})
    except ValueError as exc:
        assert "snmp_oid_set payload" in str(exc)
        return
    raise AssertionError("expected snmp_oid_set validation error")


def test_edge_job_result_schema_rejects_invalid_status() -> None:
    try:
        EdgeJobResultRequest(status="queued")
    except ValueError as exc:
        assert "unsupported edge job result status" in str(exc)
        return
    raise AssertionError("expected edge job result status validation error")


def test_edge_heartbeat_schema_rejects_invalid_status() -> None:
    try:
        EdgeNodeHeartbeatRequest(status="rooted")
    except ValueError as exc:
        assert "unsupported edge node status" in str(exc)
        return
    raise AssertionError("expected edge node status validation error")


def test_register_node_rejects_unknown_site_code() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        service = EdgeRuntimeService(db)
        try:
            service.register_node(
                name="factory-edge-01",
                site_code="UNKNOWN-SITE",
                hostname="host",
                software_version="0.1.0",
            )
        except ValueError as exc:
            assert "unknown site_code" in str(exc)
            return
        raise AssertionError("expected unknown site_code validation error")


def test_claim_next_job_returns_oldest_queued_job() -> None:
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
        db.commit()

        node = EdgeNode(
            site_id=site.id,
            name="factory-edge-01",
            node_key="edge-key",
            hostname="host",
            status="online",
        )
        db.add(node)
        db.commit()
        db.refresh(node)

        service = EdgeRuntimeService(db)
        first = service.enqueue_edge_job(edge_node_id=node.id, job_kind="scan", payload={"scan_subnets": ["10.0.0.0/24"]})
        second = service.enqueue_edge_job(edge_node_id=node.id, job_kind="dbus-demo", payload=None)

        claimed = service.claim_next_job(node=node)

        assert claimed is not None
        assert claimed.id == first.id
        assert claimed.id != second.id
