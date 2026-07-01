from sqlalchemy.orm import Session

from dynamic_alert.config import Settings, get_settings
from dynamic_alert.database import SessionLocal
from dynamic_alert.services.audit import AuditLogService
from dynamic_alert.services.background_jobs import BackgroundJob, get_background_job_runner
from dynamic_alert.services.discovery import NetworkDiscoveryService
from dynamic_alert.services.ingestion import IngestionCoordinator
from dynamic_alert.services.job_execution import (
    execute_dbus_demo,
    execute_live_capture,
    execute_passive_observe,
    execute_scan,
)
from dynamic_alert.services.passive_observation import PassiveObservationService
from dynamic_alert.services.protocols.mqtt import MqttAdapter
from dynamic_alert.services.protocols.dbus import DBusAdapter
from dynamic_alert.services.protocols.modbus import ModbusAdapter
from dynamic_alert.services.protocols.opcua import OpcUaAdapter
from dynamic_alert.services.protocols.registry import ProtocolRegistry
from dynamic_alert.services.protocols.snmp import SnmpAdapter
from dynamic_alert.services.protocols.tcp import TcpAdapter
from dynamic_alert.services.rule_engine import RuleEngine
from dynamic_alert.services.semantic_intelligence import SemanticIntelligenceService
from dynamic_alert.services.telegram import TelegramNotifier

PROTOCOL_ADAPTER_ORDER = [
    "modbus_tcp",
    "snmp",
    "mqtt",
    "opc_ua",
    "dbus_gateway",
    "raw_tcp",
]


def create_protocol_registry(settings: Settings, *, enabled_protocol_names: list[str] | None = None) -> ProtocolRegistry:
    registry = ProtocolRegistry(
        [
            ModbusAdapter(settings),
            SnmpAdapter(settings),
            MqttAdapter(settings),
            OpcUaAdapter(settings),
            DBusAdapter(),
            TcpAdapter(),
        ]
    )
    return registry.select(enabled_protocol_names)


def create_ingestion_coordinator(
    db: Session,
    *,
    settings: Settings | None = None,
    discovery: NetworkDiscoveryService | None = None,
    enabled_protocol_names: list[str] | None = None,
) -> IngestionCoordinator:
    settings = settings or get_settings()
    notifier = TelegramNotifier(settings)
    rule_engine = RuleEngine(db, notifier)
    semantic_intelligence = SemanticIntelligenceService(db, settings)
    discovery = discovery or NetworkDiscoveryService(settings.scan_subnets)
    protocol_registry = create_protocol_registry(settings, enabled_protocol_names=enabled_protocol_names)
    return IngestionCoordinator(db, discovery, protocol_registry, rule_engine, semantic_intelligence)


def get_ingestion_coordinator(db: Session) -> IngestionCoordinator:
    return create_ingestion_coordinator(db)


def enqueue_scan_job(*, actor: str) -> BackgroundJob:
    runner = get_background_job_runner()
    return runner.submit(kind="scan", actor=actor, task=lambda: _run_scan_job(actor))


def enqueue_passive_observe_job(*, actor: str) -> BackgroundJob:
    runner = get_background_job_runner()
    return runner.submit(kind="passive-observe", actor=actor, task=lambda: _run_passive_observe_job(actor))


def enqueue_live_capture_job(*, actor: str) -> BackgroundJob:
    runner = get_background_job_runner()
    return runner.submit(kind="live-capture", actor=actor, task=lambda: _run_live_capture_job(actor))


def enqueue_dbus_demo_job(*, actor: str) -> BackgroundJob:
    runner = get_background_job_runner()
    return runner.submit(kind="dbus-demo", actor=actor, task=lambda: _run_dbus_demo_job(actor))


def _run_scan_job(actor: str) -> dict[str, int]:
    db = SessionLocal()
    try:
        result = execute_scan(get_ingestion_coordinator(db))
        AuditLogService(db).record(actor=actor, action="scan.run", target="network", details=str(result))
        return result
    finally:
        db.close()


def _run_passive_observe_job(actor: str) -> dict[str, int]:
    db = SessionLocal()
    try:
        result = execute_passive_observe(PassiveObservationService(db, get_settings()))
        AuditLogService(db).record(actor=actor, action="observe.demo", target="traffic", details=str(result))
        return result
    finally:
        db.close()


def _run_live_capture_job(actor: str) -> dict[str, int]:
    db = SessionLocal()
    try:
        result = execute_live_capture(PassiveObservationService(db, get_settings()))
        AuditLogService(db).record(actor=actor, action="capture.live", target="traffic", details=str(result))
        return result
    finally:
        db.close()


def _run_dbus_demo_job(actor: str) -> dict[str, int]:
    db = SessionLocal()
    try:
        result = execute_dbus_demo(get_ingestion_coordinator(db))
        AuditLogService(db).record(
            actor=actor,
            action="demo.dbus-temperature-alert",
            target="dbus_gateway",
            details=str(result),
        )
        return result
    finally:
        db.close()
