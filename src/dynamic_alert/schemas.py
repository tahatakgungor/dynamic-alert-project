from datetime import datetime

from pydantic import BaseModel


class DeviceRead(BaseModel):
    id: int
    site_id: int | None
    ip_address: str
    hostname: str | None
    vendor: str | None
    status: str

    class Config:
        from_attributes = True


class TelemetryRead(BaseModel):
    id: int
    device_id: int
    metric_key: str
    value: float
    unit: str | None
    quality: str
    source_protocol: str
    observed_at: datetime

    class Config:
        from_attributes = True


class AlertRuleCreate(BaseModel):
    name: str
    metric_key: str
    operator: str
    threshold: float
    severity: str = "warning"
    enabled: bool = True
    notification_channel: str = "telegram"


class AlertRuleRead(AlertRuleCreate):
    id: int

    class Config:
        from_attributes = True


class WorkspaceRead(BaseModel):
    id: int
    name: str
    slug: str

    class Config:
        from_attributes = True


class SiteRead(BaseModel):
    id: int
    workspace_id: int
    name: str
    code: str
    timezone: str

    class Config:
        from_attributes = True


class IntegrationEndpointRead(BaseModel):
    id: int
    site_id: int
    name: str
    kind: str
    status: str
    target_ref: str | None

    class Config:
        from_attributes = True
