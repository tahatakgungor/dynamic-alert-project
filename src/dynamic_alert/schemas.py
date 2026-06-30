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


class SemanticHypothesisRead(BaseModel):
    id: int
    device_id: int
    raw_metric_key: str
    predicted_metric_key: str
    predicted_unit: str | None
    confidence: float
    evidence: str
    learning_state: str
    last_observed_value: float | None
    observation_count: int

    class Config:
        from_attributes = True


class SemanticMapCreate(BaseModel):
    scope: str = "device"
    device_id: int | None = None
    vendor: str | None = None
    protocol_name: str
    source_key: str
    metric_key: str
    unit: str | None = None
    notes: str | None = None


class SemanticMapRead(SemanticMapCreate):
    id: int
    confidence: float
    source_kind: str

    class Config:
        from_attributes = True
