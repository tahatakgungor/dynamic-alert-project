import json

from fastapi import APIRouter, Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from dynamic_alert.auth import AuthContext, get_auth_context, require_admin, require_operator
from dynamic_alert.config import get_settings
from dynamic_alert.database import get_db
from dynamic_alert.models import (
    AlertEvent,
    AlertRule,
    AuditLog,
    ApiClient,
    BackgroundJobRecord,
    Device,
    EdgeJob,
    EdgeNode,
    FlowCluster,
    IntegrationEndpoint,
    SemanticMap,
    SemanticHypothesis,
    Site,
    TelemetryRecord,
    TrafficObservation,
    UnknownProtocolCandidate,
    Workspace,
)
from dynamic_alert.schemas import (
    AlertRuleCreate,
    AlertRuleRead,
    DeviceRead,
    EdgeJobCreate,
    EdgeJobResultRequest,
    EdgeNodeHeartbeatRequest,
    EdgeNodeRead,
    EdgeNodeRegisterRequest,
    IntegrationEndpointRead,
    SemanticHypothesisPromoteRequest,
    SemanticMapCreate,
    SemanticMapRead,
    SemanticHypothesisRead,
    SiteRead,
    TelemetryRead,
    UnknownCandidateActionRequest,
    WorkspaceRead,
)
from dynamic_alert.services.background_jobs import get_background_job_runner
from dynamic_alert.services.container import (
    enqueue_dbus_demo_job,
    enqueue_live_capture_job,
    enqueue_passive_observe_job,
    enqueue_scan_job,
)
from dynamic_alert.services.audit import AuditLogService
from dynamic_alert.services.passive_observation import PassiveObservationService
from dynamic_alert.services.edge_runtime import EdgeRuntimeService
from dynamic_alert.services.semantic_map import SemanticMapService
from dynamic_alert.services.traffic_intelligence import TrafficIntelligenceService

router = APIRouter()
templates = Jinja2Templates(directory="templates")
edge_key_header = APIKeyHeader(name="X-Edge-Key", auto_error=False)


def get_edge_node(
    edge_key: str | None = Security(edge_key_header),
    db: Session = Depends(get_db),
) -> EdgeNode:
    if not edge_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing edge key")
    node = EdgeRuntimeService(db).authenticate_node(edge_key)
    if node is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid edge key")
    return node


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    jobs = [
        item.to_dict()
        for item in get_background_job_runner().list_recent(limit=10)
    ]
    devices = db.query(Device).order_by(Device.created_at.desc()).limit(10).all()
    telemetry = db.query(TelemetryRecord).order_by(TelemetryRecord.observed_at.desc()).limit(20).all()
    rules = db.query(AlertRule).order_by(AlertRule.id.desc()).limit(20).all()
    sites = db.query(Site).order_by(Site.id.desc()).limit(10).all()
    integrations = db.query(IntegrationEndpoint).order_by(IntegrationEndpoint.id.desc()).limit(10).all()
    edge_nodes = db.query(EdgeNode).order_by(EdgeNode.last_seen_at.desc().nullslast()).limit(10).all()
    edge_jobs = db.query(EdgeJob).order_by(EdgeJob.created_at.desc()).limit(10).all()
    semantic_hypotheses = db.query(SemanticHypothesis).order_by(SemanticHypothesis.id.desc()).limit(10).all()
    semantic_maps = db.query(SemanticMap).order_by(SemanticMap.updated_at.desc()).limit(10).all()
    flow_clusters = db.query(FlowCluster).order_by(FlowCluster.updated_at.desc()).limit(10).all()
    unknown_candidates = db.query(UnknownProtocolCandidate).order_by(UnknownProtocolCandidate.updated_at.desc()).limit(10).all()
    alert_events = db.query(AlertEvent).order_by(AlertEvent.created_at.desc()).limit(10).all()
    audit_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(12).all()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "devices": devices,
            "telemetry": telemetry,
            "rules": rules,
            "sites": sites,
            "integrations": integrations,
            "edge_nodes": edge_nodes,
            "edge_jobs": edge_jobs,
            "semantic_hypotheses": semantic_hypotheses,
            "semantic_maps": semantic_maps,
            "flow_clusters": flow_clusters,
            "unknown_candidates": unknown_candidates,
            "alert_events": alert_events,
            "audit_logs": audit_logs,
            "jobs": jobs,
        },
    )


@router.post("/api/scan")
def run_scan(auth: AuthContext = Depends(require_operator)) -> dict[str, str]:
    job = enqueue_scan_job(actor=auth.name)
    return {"job_id": job.id, "status": job.status, "job_kind": job.kind}


@router.post("/api/passive-observe")
def run_passive_observe(
    auth: AuthContext = Depends(require_operator),
    _: Session = Depends(get_db),
) -> dict[str, str]:
    job = enqueue_passive_observe_job(actor=auth.name)
    return {"job_id": job.id, "status": job.status, "job_kind": job.kind}


@router.post("/api/live-capture")
def run_live_capture(
    auth: AuthContext = Depends(require_operator),
    _: Session = Depends(get_db),
) -> dict[str, str]:
    job = enqueue_live_capture_job(actor=auth.name)
    return {"job_id": job.id, "status": job.status, "job_kind": job.kind}


@router.get("/api/devices", response_model=list[DeviceRead])
def list_devices(db: Session = Depends(get_db)) -> list[Device]:
    return db.query(Device).order_by(Device.created_at.desc()).all()


@router.get("/api/telemetry", response_model=list[TelemetryRead])
def list_telemetry(db: Session = Depends(get_db)) -> list[TelemetryRecord]:
    return db.query(TelemetryRecord).order_by(TelemetryRecord.observed_at.desc()).limit(100).all()


@router.get("/api/rules", response_model=list[AlertRuleRead])
def list_rules(db: Session = Depends(get_db)) -> list[AlertRule]:
    return db.query(AlertRule).order_by(AlertRule.id.desc()).all()


@router.get("/api/workspaces", response_model=list[WorkspaceRead])
def list_workspaces(db: Session = Depends(get_db)) -> list[Workspace]:
    return db.query(Workspace).order_by(Workspace.id.desc()).all()


@router.get("/api/sites", response_model=list[SiteRead])
def list_sites(db: Session = Depends(get_db)) -> list[Site]:
    return db.query(Site).order_by(Site.id.desc()).all()


@router.get("/api/integrations", response_model=list[IntegrationEndpointRead])
def list_integrations(db: Session = Depends(get_db)) -> list[IntegrationEndpoint]:
    return db.query(IntegrationEndpoint).order_by(IntegrationEndpoint.id.desc()).all()


@router.get("/api/edge-nodes", response_model=list[EdgeNodeRead])
def list_edge_nodes(
    _: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[EdgeNode]:
    return db.query(EdgeNode).order_by(EdgeNode.last_seen_at.desc().nullslast()).all()


@router.post("/api/edge/register")
def register_edge_node(
    payload: EdgeNodeRegisterRequest,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, str | int | None]:
    try:
        node, node_key = EdgeRuntimeService(db).register_node(
            name=payload.name,
            site_code=payload.site_code,
            hostname=payload.hostname,
            software_version=payload.software_version,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    AuditLogService(db).record(
        actor=auth.name,
        action="edge-node.register",
        target=node.name,
        details=payload.site_code or "-",
    )
    return {"id": node.id, "name": node.name, "node_key": node_key, "site_id": node.site_id}


@router.post("/api/edge/heartbeat", response_model=EdgeNodeRead)
def edge_heartbeat(
    payload: EdgeNodeHeartbeatRequest,
    node: EdgeNode = Depends(get_edge_node),
    db: Session = Depends(get_db),
) -> EdgeNode:
    return EdgeRuntimeService(db).heartbeat(node=node, status=payload.status, software_version=payload.software_version)


@router.post("/api/edge-jobs")
def create_edge_job(
    payload: EdgeJobCreate,
    auth: AuthContext = Depends(require_operator),
    db: Session = Depends(get_db),
) -> dict[str, str | int | None]:
    try:
        job = EdgeRuntimeService(db).enqueue_edge_job(
            edge_node_id=payload.edge_node_id,
            job_kind=payload.job_kind,
            payload=payload.payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    AuditLogService(db).record(
        actor=auth.name,
        action="edge-job.enqueue",
        target=f"edge-node:{payload.edge_node_id}",
        details=payload.job_kind,
    )
    return {"id": job.id, "edge_node_id": job.edge_node_id, "status": job.status, "job_kind": job.job_kind}


@router.get("/api/edge-jobs")
def list_edge_jobs(
    _: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[dict[str, str | int | None]]:
    jobs = db.query(EdgeJob).order_by(EdgeJob.created_at.desc()).limit(100).all()
    return [
        {
            "id": item.id,
            "edge_node_id": item.edge_node_id,
            "job_kind": item.job_kind,
            "status": item.status,
            "payload": json.loads(item.payload_json) if item.payload_json else None,
            "error": item.error,
        }
        for item in jobs
    ]


@router.post("/api/edge/claim-next-job")
def claim_next_edge_job(
    node: EdgeNode = Depends(get_edge_node),
    db: Session = Depends(get_db),
) -> dict[str, str | int | dict | None]:
    job = EdgeRuntimeService(db).claim_next_job(node=node)
    if job is None:
        return {"status": "empty"}
    return {
        "id": job.id,
        "edge_node_id": job.edge_node_id,
        "job_kind": job.job_kind,
        "status": job.status,
        "payload": json.loads(job.payload_json) if job.payload_json else None,
    }


@router.post("/api/edge-jobs/{job_id}/complete")
def complete_edge_job(
    job_id: int,
    payload: EdgeJobResultRequest,
    node: EdgeNode = Depends(get_edge_node),
    db: Session = Depends(get_db),
) -> dict[str, str | int | None]:
    job = EdgeRuntimeService(db).complete_job(
        node=node,
        job_id=job_id,
        status=payload.status,
        result=payload.result,
        error=payload.error,
    )
    AuditLogService(db).record(
        actor=node.name,
        action="edge-job.complete",
        target=f"edge-job:{job.id}",
        details=job.status,
    )
    return {"id": job.id, "status": job.status, "error": job.error}


@router.get("/api/semantic-hypotheses", response_model=list[SemanticHypothesisRead])
def list_semantic_hypotheses(
    _: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[SemanticHypothesis]:
    return db.query(SemanticHypothesis).order_by(SemanticHypothesis.updated_at.desc()).all()


@router.get("/api/semantic-maps", response_model=list[SemanticMapRead])
def list_semantic_maps(
    _: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[SemanticMap]:
    return db.query(SemanticMap).order_by(SemanticMap.updated_at.desc()).all()


@router.post("/api/semantic-maps", response_model=SemanticMapRead)
def create_semantic_map(
    payload: SemanticMapCreate,
    auth: AuthContext = Depends(require_operator),
    db: Session = Depends(get_db),
) -> SemanticMap:
    mapped = SemanticMapService(db).upsert_operator_map(**payload.model_dump())
    AuditLogService(db).record(
        actor=auth.name,
        action="semantic-map.upsert",
        target=f"{mapped.protocol_name}:{mapped.source_key}",
        details=mapped.metric_key,
    )
    return mapped


@router.post("/api/semantic-hypotheses/{hypothesis_id}/promote", response_model=SemanticMapRead)
def promote_semantic_hypothesis(
    hypothesis_id: int,
    payload: SemanticHypothesisPromoteRequest,
    auth: AuthContext = Depends(require_operator),
    db: Session = Depends(get_db),
) -> SemanticMap:
    mapped = SemanticMapService(db).promote_hypothesis(
        hypothesis_id=hypothesis_id,
        scope=payload.scope,
        metric_key=payload.metric_key,
        unit=payload.unit,
        notes=payload.notes,
    )
    AuditLogService(db).record(
        actor=auth.name,
        action="semantic-hypothesis.promote",
        target=f"{mapped.protocol_name}:{mapped.source_key}",
        details=mapped.metric_key,
    )
    return mapped


@router.get("/api/flow-clusters")
def list_flow_clusters(
    _: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[dict[str, str | int | None]]:
    clusters = db.query(FlowCluster).order_by(FlowCluster.updated_at.desc()).all()
    return [
        {
            "id": item.id,
            "cluster_key": item.cluster_key,
            "protocol_hint": item.protocol_hint,
            "source_ip": item.source_ip,
            "destination_ip": item.destination_ip,
            "destination_port": item.destination_port,
            "transport": item.transport,
            "sample_count": item.sample_count,
        }
        for item in clusters
    ]


@router.get("/api/traffic-observations")
def list_traffic_observations(
    _: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[dict[str, str | int | None]]:
    items = db.query(TrafficObservation).order_by(TrafficObservation.observed_at.desc()).limit(100).all()
    return [
        {
            "id": item.id,
            "source_ip": item.source_ip,
            "source_port": item.source_port,
            "destination_ip": item.destination_ip,
            "destination_port": item.destination_port,
            "transport": item.transport,
            "protocol_hint": item.protocol_hint,
            "payload_sample": item.payload_sample,
        }
        for item in items
    ]


@router.get("/api/unknown-protocol-candidates")
def list_unknown_protocol_candidates(
    _: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[dict[str, str | int | float | None]]:
    items = db.query(UnknownProtocolCandidate).order_by(UnknownProtocolCandidate.updated_at.desc()).all()
    return [
        {
            "id": item.id,
            "flow_cluster_id": item.flow_cluster_id,
            "candidate_label": item.candidate_label,
            "confidence": item.confidence,
            "evidence": item.evidence,
            "payload_fingerprint": item.payload_fingerprint,
            "status": item.status,
        }
        for item in items
    ]


@router.post("/api/unknown-protocol-candidates/{candidate_id}/action")
def apply_unknown_protocol_candidate_action(
    candidate_id: int,
    payload: UnknownCandidateActionRequest,
    auth: AuthContext = Depends(require_operator),
    db: Session = Depends(get_db),
) -> dict[str, str | int | float | None]:
    candidate = TrafficIntelligenceService(db).apply_candidate_action(
        candidate_id=candidate_id,
        action=payload.action,
        candidate_label=payload.candidate_label,
        notes=payload.notes,
    )
    AuditLogService(db).record(
        actor=auth.name,
        action=f"unknown-candidate.{payload.action}",
        target=f"candidate:{candidate.id}",
        details=f"{candidate.candidate_label} | {payload.notes or '-'}",
    )
    return {
        "id": candidate.id,
        "flow_cluster_id": candidate.flow_cluster_id,
        "candidate_label": candidate.candidate_label,
        "confidence": candidate.confidence,
        "evidence": candidate.evidence,
        "payload_fingerprint": candidate.payload_fingerprint,
        "status": candidate.status,
    }


@router.get("/api/alert-events")
def list_alert_events(
    _: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[dict[str, str | int | bool | None]]:
    items = db.query(AlertEvent).order_by(AlertEvent.created_at.desc()).limit(100).all()
    return [
        {
            "id": item.id,
            "rule_id": item.rule_id,
            "telemetry_id": item.telemetry_id,
            "message": item.message,
            "delivered": item.delivered,
            "created_at": item.created_at.isoformat(),
        }
        for item in items
    ]


@router.get("/api/audit-logs")
def list_audit_logs(
    _: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[dict[str, str | int | None]]:
    items = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
    return [
        {
            "id": item.id,
            "actor": item.actor,
            "action": item.action,
            "target": item.target,
            "status": item.status,
            "details": item.details,
            "created_at": item.created_at.isoformat(),
        }
        for item in items
    ]


@router.get("/api/auth/me")
def who_am_i(auth: AuthContext = Depends(get_auth_context)) -> dict[str, str | int]:
    return {"client_id": auth.client_id, "name": auth.name, "role": auth.role}


@router.get("/api/jobs")
def list_jobs(_: AuthContext = Depends(get_auth_context)) -> list[dict[str, str | dict | None]]:
    return [job.to_dict() for job in get_background_job_runner().list_recent(limit=100)]


@router.get("/api/jobs/{job_id}")
def get_job(job_id: str, _: AuthContext = Depends(get_auth_context)) -> dict[str, str | dict | None]:
    job = get_background_job_runner().get(job_id)
    if job is None:
        return {"id": job_id, "status": "missing", "error": "job not found"}
    return job.to_dict()


@router.get("/api/admin/api-clients")
def list_api_clients(
    _: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict[str, str | int | bool]]:
    clients = db.query(ApiClient).order_by(ApiClient.id.desc()).all()
    return [
        {"id": item.id, "name": item.name, "role": item.role, "enabled": item.enabled}
        for item in clients
    ]


@router.post("/api/rules", response_model=AlertRuleRead)
def create_rule(
    payload: AlertRuleCreate,
    auth: AuthContext = Depends(require_operator),
    db: Session = Depends(get_db),
) -> AlertRule:
    rule = AlertRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    AuditLogService(db).record(actor=auth.name, action="rule.create", target=rule.name, details=rule.metric_key)
    return rule


@router.post("/api/demo/dbus-temperature-alert")
def run_dbus_temperature_demo(
    auth: AuthContext = Depends(require_operator),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    rule = db.query(AlertRule).filter(AlertRule.name == "demo_dbus_temperature_high").one_or_none()
    if rule is None:
        db.add(
            AlertRule(
                name="demo_dbus_temperature_high",
                metric_key="temperature_c",
                operator=">=",
                threshold=70.0,
                severity="critical",
                enabled=True,
                notification_channel="telegram",
            )
        )
        db.commit()

    job = enqueue_dbus_demo_job(actor=auth.name)
    return {"job_id": job.id, "status": job.status, "job_kind": job.kind}
