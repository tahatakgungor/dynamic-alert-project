from __future__ import annotations

from datetime import datetime
import json
import secrets

from sqlalchemy.orm import Session

from dynamic_alert.models import EdgeJob, EdgeNode, Site


class EdgeRuntimeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def register_node(
        self,
        *,
        name: str,
        site_code: str | None,
        hostname: str | None,
        software_version: str | None,
    ) -> tuple[EdgeNode, str]:
        node = self.db.query(EdgeNode).filter(EdgeNode.name == name).one_or_none()
        site = self.db.query(Site).filter(Site.code == site_code).one_or_none() if site_code else None
        if site_code and site is None:
            raise ValueError(f"unknown site_code: {site_code}")
        generated_key = secrets.token_urlsafe(24)

        if node is None:
            node = EdgeNode(
                site_id=site.id if site else None,
                name=name,
                node_key=generated_key,
                hostname=hostname,
                status="registered",
                last_seen_at=datetime.utcnow(),
                software_version=software_version,
            )
            self.db.add(node)
        else:
            node.site_id = site.id if site else node.site_id
            node.hostname = hostname or node.hostname
            node.status = "registered"
            node.last_seen_at = datetime.utcnow()
            node.software_version = software_version or node.software_version
            generated_key = node.node_key

        self.db.commit()
        self.db.refresh(node)
        return node, generated_key

    def authenticate_node(self, node_key: str) -> EdgeNode | None:
        return self.db.query(EdgeNode).filter(EdgeNode.node_key == node_key).one_or_none()

    def heartbeat(self, *, node: EdgeNode, status: str, software_version: str | None) -> EdgeNode:
        node.status = status
        node.last_seen_at = datetime.utcnow()
        if software_version:
            node.software_version = software_version
        self.db.commit()
        self.db.refresh(node)
        return node

    def enqueue_edge_job(self, *, edge_node_id: int, job_kind: str, payload: dict | None) -> EdgeJob:
        node = self.db.query(EdgeNode).filter(EdgeNode.id == edge_node_id).one_or_none()
        if node is None:
            raise ValueError(f"unknown edge_node_id: {edge_node_id}")
        job = EdgeJob(
            edge_node_id=edge_node_id,
            job_kind=job_kind,
            status="queued",
            payload_json=json.dumps(payload) if payload is not None else None,
            created_at=datetime.utcnow(),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def claim_next_job(self, *, node: EdgeNode) -> EdgeJob | None:
        job = (
            self.db.query(EdgeJob)
            .filter(EdgeJob.edge_node_id == node.id, EdgeJob.status == "queued")
            .order_by(EdgeJob.created_at.asc())
            .first()
        )
        if job is None:
            return None
        job.status = "running"
        job.claimed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job

    def complete_job(self, *, node: EdgeNode, job_id: int, status: str, result: dict | None, error: str | None) -> EdgeJob:
        job = (
            self.db.query(EdgeJob)
            .filter(EdgeJob.id == job_id, EdgeJob.edge_node_id == node.id)
            .one()
        )
        if job.status in {"completed", "failed"}:
            raise ValueError(f"edge job already finalized: {job.status}")
        if job.status != "running":
            raise ValueError(f"edge job is not running: {job.status}")
        job.status = status
        job.result_json = json.dumps(result) if result is not None else None
        job.error = error
        job.finished_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job
