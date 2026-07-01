from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert.database import Base
from dynamic_alert.models import EdgeJob, EdgeNode, Site, Workspace
from dynamic_alert.services.edge_runtime import EdgeRuntimeService


def test_edge_node_register_and_job_lifecycle() -> None:
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

        service = EdgeRuntimeService(db)
        node, node_key = service.register_node(
            name="factory-edge-01",
            site_code="HQ-PLANT",
            hostname="factory-edge-host",
            software_version="0.1.0",
        )
        assert node_key
        assert node.site_id == site.id

        auth_node = service.authenticate_node(node_key)
        assert auth_node is not None
        assert auth_node.name == "factory-edge-01"

        heartbeat = service.heartbeat(node=auth_node, status="online", software_version="0.1.1")
        assert heartbeat.status == "online"
        assert heartbeat.software_version == "0.1.1"

        job = service.enqueue_edge_job(
            edge_node_id=node.id,
            job_kind="scan",
            payload={"segment": "192.168.1.0/24"},
        )
        assert job.status == "queued"

        claimed = service.claim_next_job(node=node)
        assert claimed is not None
        assert claimed.id == job.id
        assert claimed.status == "running"

        completed = service.complete_job(
            node=node,
            job_id=job.id,
            status="completed",
            result={"new_devices": 2},
            error=None,
        )
        assert completed.status == "completed"

        assert db.query(EdgeNode).count() == 1
        assert db.query(EdgeJob).count() == 1
