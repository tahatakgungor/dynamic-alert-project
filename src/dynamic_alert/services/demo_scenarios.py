from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy.orm import Session

from dynamic_alert.config import Settings
from dynamic_alert.models import AlertEvent, AlertRule, SemanticHypothesis, TelemetryRecord
from dynamic_alert.services.container import create_ingestion_coordinator
from dynamic_alert.services.discovery import DiscoveredDevice
from dynamic_alert.services.job_execution import execute_dbus_demo
from dynamic_alert.services.passive_observation import PacketSample, PassiveObservationService
from dynamic_alert.services.protocols.base import FingerprintResult, ProtocolAdapter
from dynamic_alert.services.protocols.modbus import ModbusAdapter
from dynamic_alert.services.protocols.registry import ProtocolRegistry


@dataclass(slots=True)
class DemoScenario:
    key: str
    title: str
    category: str
    description: str
    expected: str


SCENARIOS = [
    DemoScenario(
        key="dbus_temperature_alert",
        title="D-Bus Sicaklik Alarmi",
        category="alert",
        description="Linux edge gateway uzerinden gelen yuksek sicaklik telemetry'si semantic yorum ve alarm zincirini tetikler.",
        expected="Yeni telemetry, semantic hypothesis ve alert event gorunmeli.",
    ),
    DemoScenario(
        key="modbus_catalog_alert",
        title="Modbus Kataloglu Termal Loop",
        category="protocol",
        description="Named Modbus profile set ile bir thermal-loop PLC sicaklik metriği okunur ve semantic alert akisi tetiklenir.",
        expected="Modbus fingerprint, telemetry ve temperature_c alarmi gorunmeli.",
    ),
    DemoScenario(
        key="passive_unknown_protocol",
        title="Passive Unknown Protocol",
        category="forensics",
        description="Ham trafik ornegi flow cluster ve unknown protocol candidate uretir; audit ve operator akisinda incelenebilir.",
        expected="Yeni unknown candidate ve flow cluster gorunmeli.",
    ),
]


def list_demo_scenarios() -> list[dict[str, str]]:
    return [asdict(item) for item in SCENARIOS]


def run_demo_scenario(db: Session, settings: Settings, key: str) -> dict[str, object]:
    if key == "dbus_temperature_alert":
        _ensure_temperature_rule(db, name="demo_dbus_temperature_high")
        result = execute_dbus_demo(
            create_ingestion_coordinator(
                db,
                settings=settings,
                enabled_protocol_names=["dbus_gateway"],
            ),
            {
                "site_code": "HQ-PLANT",
                "ip_address": "192.168.10.50",
                "hostname": "edge-temp-gw",
                "vendor": "Linux Edge Gateway",
                "open_ports": [22, 80],
            },
        )
        return _build_summary(db, key=key, result=result)

    if key == "modbus_catalog_alert":
        _ensure_temperature_rule(db, name="demo_modbus_catalog_temperature_high")
        replay_registry = ProtocolRegistry([CatalogReplayModbusAdapter(settings)])
        coordinator = create_ingestion_coordinator(
            db,
            settings=settings.model_copy(update={"modbus_profile_set": "generic_plc"}),
            enabled_protocol_names=["modbus_tcp"],
        )
        coordinator.protocol_registry = replay_registry
        result = coordinator.ingest_device(
            DiscoveredDevice(
                site_code="HQ-PLANT",
                ip_address="10.20.30.20",
                hostname="thermal-loop-01",
                vendor="Generic PLC",
                open_ports={502},
            )
        )
        return _build_summary(
            db,
            key=key,
            result=result,
            metadata={"modbus_profile_set": "generic_plc"},
        )

    if key == "passive_unknown_protocol":
        service = PassiveObservationService(db, settings)
        result = service.ingest_samples(
            [
                PacketSample(
                    source_ip="10.20.30.10",
                    source_port=41000,
                    destination_ip="10.20.30.40",
                    destination_port=44818,
                    transport="tcp",
                    payload_sample="5345572d48454c4c4f205441475f554e4b4e4f574e",
                )
            ]
        )
        return _build_summary(db, key=key, result=result)

    raise ValueError(f"unsupported demo scenario: {key}")


class CatalogReplayModbusAdapter(ProtocolAdapter):
    name = "modbus_tcp"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._delegate = ModbusAdapter(settings)

    def matches(self, open_ports: set[int]) -> bool:
        return 502 in open_ports

    def fingerprint(self, ip_address: str, open_ports: set[int]) -> FingerprintResult:
        return self._delegate.fingerprint(ip_address, open_ports)

    def collect_telemetry(self, device: DiscoveredDevice) -> list[dict]:
        profiles = self._delegate.profile_repository.match(device, profile_set=self.settings.modbus_profile_set)
        if not profiles:
            return []
        return self._delegate._read_profiles(_ReplayModbusClient(), profiles)


class _ReplayResponse:
    def __init__(self, registers: list[int]) -> None:
        self.registers = registers

    def isError(self) -> bool:
        return False


class _ReplayModbusClient:
    def read_holding_registers(self, *, address: int, count: int, **_: object) -> _ReplayResponse:
        mapping = {
            0: [815],
            1: [52],
            10: [784],
        }
        registers = mapping.get(address, [0] * count)
        return _ReplayResponse(registers[:count])

    read_input_registers = read_holding_registers


def _ensure_temperature_rule(db: Session, *, name: str) -> None:
    existing = db.query(AlertRule).filter(AlertRule.name == name).one_or_none()
    if existing is not None:
        return
    db.add(
        AlertRule(
            name=name,
            metric_key="temperature_c",
            operator=">=",
            threshold=70.0,
            severity="critical",
            enabled=True,
            notification_channel="telegram",
        )
    )
    db.commit()


def _build_summary(
    db: Session,
    *,
    key: str,
    result: dict[str, object],
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    latest_alert = db.query(AlertEvent).order_by(AlertEvent.id.desc()).first()
    latest_telemetry = db.query(TelemetryRecord).order_by(TelemetryRecord.id.desc()).first()
    latest_hypothesis = db.query(SemanticHypothesis).order_by(SemanticHypothesis.id.desc()).first()
    if latest_alert is not None:
        alert_telemetry = db.query(TelemetryRecord).filter(TelemetryRecord.id == latest_alert.telemetry_id).one_or_none()
        if alert_telemetry is not None:
            latest_telemetry = alert_telemetry
            latest_hypothesis = (
                db.query(SemanticHypothesis)
                .filter(
                    SemanticHypothesis.device_id == alert_telemetry.device_id,
                    SemanticHypothesis.raw_metric_key == alert_telemetry.metric_key,
                )
                .order_by(SemanticHypothesis.id.desc())
                .first()
            )
    summary: dict[str, object] = {
        "scenario_key": key,
        "result": result,
        "latest_telemetry": None,
        "latest_semantic": None,
        "latest_alert": None,
    }
    if latest_telemetry is not None:
        summary["latest_telemetry"] = {
            "metric_key": latest_telemetry.metric_key,
            "value": latest_telemetry.value,
            "unit": latest_telemetry.unit,
            "source_protocol": latest_telemetry.source_protocol,
        }
    if latest_hypothesis is not None:
        summary["latest_semantic"] = {
            "raw_metric_key": latest_hypothesis.raw_metric_key,
            "predicted_metric_key": latest_hypothesis.predicted_metric_key,
            "learning_state": latest_hypothesis.learning_state,
        }
    if latest_alert is not None:
        summary["latest_alert"] = {
            "message": latest_alert.message,
            "delivered": latest_alert.delivered,
        }
    if metadata:
        summary["metadata"] = metadata
    return summary
