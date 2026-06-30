from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from dynamic_alert.database import get_db
from dynamic_alert.models import AlertRule, Device, IntegrationEndpoint, Site, TelemetryRecord, Workspace
from dynamic_alert.schemas import (
    AlertRuleCreate,
    AlertRuleRead,
    DeviceRead,
    IntegrationEndpointRead,
    SiteRead,
    TelemetryRead,
    WorkspaceRead,
)
from dynamic_alert.services.container import get_ingestion_coordinator

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    devices = db.query(Device).order_by(Device.created_at.desc()).limit(10).all()
    telemetry = db.query(TelemetryRecord).order_by(TelemetryRecord.observed_at.desc()).limit(20).all()
    rules = db.query(AlertRule).order_by(AlertRule.id.desc()).limit(20).all()
    sites = db.query(Site).order_by(Site.id.desc()).limit(10).all()
    integrations = db.query(IntegrationEndpoint).order_by(IntegrationEndpoint.id.desc()).limit(10).all()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "devices": devices,
            "telemetry": telemetry,
            "rules": rules,
            "sites": sites,
            "integrations": integrations,
        },
    )


@router.post("/api/scan")
def run_scan(db: Session = Depends(get_db)) -> dict[str, int]:
    coordinator = get_ingestion_coordinator(db)
    return coordinator.run_cycle()


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


@router.post("/api/rules", response_model=AlertRuleRead)
def create_rule(payload: AlertRuleCreate, db: Session = Depends(get_db)) -> AlertRule:
    rule = AlertRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
