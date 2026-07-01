from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

ALLOWED_EDGE_JOB_KINDS = {"scan", "passive-observe", "live-capture", "dbus-demo"}
ALLOWED_EDGE_NODE_STATUSES = {"registered", "online", "degraded", "offline"}
ALLOWED_EDGE_JOB_RESULT_STATUSES = {"completed", "failed"}
ALLOWED_PROTOCOL_NAMES = {"modbus_tcp", "snmp", "mqtt", "opc_ua", "dbus_gateway", "raw_tcp"}


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int | None
    ip_address: str
    hostname: str | None
    vendor: str | None
    status: str


class TelemetryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    metric_key: str
    value: float
    unit: str | None
    quality: str
    source_protocol: str
    observed_at: datetime


class AlertRuleCreate(BaseModel):
    name: str
    metric_key: str
    operator: str
    threshold: float
    severity: str = "warning"
    enabled: bool = True
    notification_channel: str = "telegram"


class AlertRuleRead(AlertRuleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class SiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    name: str
    code: str
    timezone: str


class IntegrationEndpointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    name: str
    kind: str
    status: str
    target_ref: str | None


class SemanticHypothesisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    model_config = ConfigDict(from_attributes=True)

    id: int
    confidence: float
    source_kind: str


class SemanticHypothesisPromoteRequest(BaseModel):
    scope: str = "device"
    metric_key: str | None = None
    unit: str | None = None
    notes: str | None = None


class UnknownCandidateActionRequest(BaseModel):
    action: str
    candidate_label: str | None = None
    notes: str | None = None


class EdgeNodeRegisterRequest(BaseModel):
    name: str
    site_code: str | None = None
    hostname: str | None = None
    software_version: str | None = None


class EdgeNodeHeartbeatRequest(BaseModel):
    software_version: str | None = None
    status: str = "online"

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in ALLOWED_EDGE_NODE_STATUSES:
            raise ValueError("unsupported edge node status")
        return value


class EdgeNodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int | None
    name: str
    hostname: str | None
    status: str
    last_seen_at: datetime | None
    software_version: str | None


class EdgeNodeRegisterResponse(BaseModel):
    id: int
    name: str
    node_key: str
    site_id: int | None


class EdgeJobCreate(BaseModel):
    edge_node_id: int
    job_kind: str
    payload: dict | None = None

    @field_validator("job_kind")
    @classmethod
    def validate_job_kind(cls, value: str) -> str:
        if value not in ALLOWED_EDGE_JOB_KINDS:
            raise ValueError("unsupported edge job kind")
        return value

    @model_validator(mode="after")
    def validate_payload_shape(self) -> "EdgeJobCreate":
        if not self.payload:
            return self
        if len(str(self.payload)) > 4096:
            raise ValueError("payload is too large")
        samples = self.payload.get("samples")
        if samples is not None:
            if not isinstance(samples, list) or len(samples) > 64:
                raise ValueError("samples payload must be a list with at most 64 items")
        scan_subnets = self.payload.get("scan_subnets")
        if scan_subnets is not None:
            if not isinstance(scan_subnets, list) or len(scan_subnets) > 16:
                raise ValueError("scan_subnets payload must be a list with at most 16 entries")
        enabled_protocols = self.payload.get("enabled_protocols")
        if enabled_protocols is not None:
            if not isinstance(enabled_protocols, list) or not enabled_protocols:
                raise ValueError("enabled_protocols payload must be a non-empty list")
            if len(enabled_protocols) > len(ALLOWED_PROTOCOL_NAMES):
                raise ValueError("enabled_protocols payload is too large")
            unknown = [item for item in enabled_protocols if item not in ALLOWED_PROTOCOL_NAMES]
            if unknown:
                raise ValueError(f"unsupported protocol names: {', '.join(str(item) for item in unknown)}")
        mqtt_topics = self.payload.get("mqtt_probe_topics")
        if mqtt_topics is not None:
            if not isinstance(mqtt_topics, list) or len(mqtt_topics) > 16:
                raise ValueError("mqtt_probe_topics payload must be a list with at most 16 entries")
        mqtt_topic_set = self.payload.get("mqtt_topic_set")
        if mqtt_topic_set is not None and (not isinstance(mqtt_topic_set, str) or len(mqtt_topic_set) > 64):
            raise ValueError("mqtt_topic_set payload must be a string up to 64 chars")
        modbus_profiles_path = self.payload.get("modbus_profiles_path")
        if modbus_profiles_path is not None and (not isinstance(modbus_profiles_path, str) or len(modbus_profiles_path) > 255):
            raise ValueError("modbus_profiles_path payload must be a string up to 255 chars")
        modbus_profile_set = self.payload.get("modbus_profile_set")
        if modbus_profile_set is not None and (not isinstance(modbus_profile_set, str) or len(modbus_profile_set) > 64):
            raise ValueError("modbus_profile_set payload must be a string up to 64 chars")
        snmp_oid_set = self.payload.get("snmp_oid_set")
        if snmp_oid_set is not None and (not isinstance(snmp_oid_set, str) or len(snmp_oid_set) > 64):
            raise ValueError("snmp_oid_set payload must be a string up to 64 chars")
        for oid_key in ("snmp_oid_sysdescr", "snmp_oid_sysname", "snmp_oid_uptime"):
            oid_value = self.payload.get(oid_key)
            if oid_value is not None and (not isinstance(oid_value, str) or len(oid_value) > 128):
                raise ValueError(f"{oid_key} payload must be a string up to 128 chars")
        return self


class EdgeJobResultRequest(BaseModel):
    status: str
    result: dict | None = None
    error: str | None = None

    @field_validator("status")
    @classmethod
    def validate_result_status(cls, value: str) -> str:
        if value not in ALLOWED_EDGE_JOB_RESULT_STATUSES:
            raise ValueError("unsupported edge job result status")
        return value


class EdgeJobRead(BaseModel):
    id: int
    edge_node_id: int
    job_kind: str
    status: str
    payload: dict | None = None
    error: str | None = None


class BackgroundJobRead(BaseModel):
    id: str
    kind: str
    actor: str
    status: str
    submitted_at: str
    started_at: str | None = None
    finished_at: str | None = None
    result: dict | None = None
    error: str | None = None
