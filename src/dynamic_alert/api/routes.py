from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from dynamic_alert.database import get_db
from dynamic_alert.models import AlertRule, Device, TelemetryRecord
from dynamic_alert.schemas import AlertRuleCreate, AlertRuleRead, DeviceRead, TelemetryRead
from dynamic_alert.services.container import get_ingestion_coordinator

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    devices = db.query(Device).order_by(Device.created_at.desc()).limit(10).all()
    telemetry = db.query(TelemetryRecord).order_by(TelemetryRecord.observed_at.desc()).limit(20).all()
    rules = db.query(AlertRule).order_by(AlertRule.id.desc()).limit(20).all()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "devices": devices,
            "telemetry": telemetry,
            "rules": rules,
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


@router.post("/api/rules", response_model=AlertRuleRead)
def create_rule(payload: AlertRuleCreate, db: Session = Depends(get_db)) -> AlertRule:
    rule = AlertRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
