from sqlalchemy.orm import Session

from dynamic_alert.config import get_settings
from dynamic_alert.services.discovery import NetworkDiscoveryService
from dynamic_alert.services.ingestion import IngestionCoordinator
from dynamic_alert.services.protocols.mqtt import MqttAdapter
from dynamic_alert.services.protocols.dbus import DBusAdapter
from dynamic_alert.services.protocols.modbus import ModbusAdapter
from dynamic_alert.services.protocols.registry import ProtocolRegistry
from dynamic_alert.services.protocols.snmp import SnmpAdapter
from dynamic_alert.services.protocols.tcp import TcpAdapter
from dynamic_alert.services.rule_engine import RuleEngine
from dynamic_alert.services.semantic_intelligence import SemanticIntelligenceService
from dynamic_alert.services.telegram import TelegramNotifier


def get_ingestion_coordinator(db: Session) -> IngestionCoordinator:
    settings = get_settings()
    notifier = TelegramNotifier(settings)
    rule_engine = RuleEngine(db, notifier)
    semantic_intelligence = SemanticIntelligenceService(db, settings)
    discovery = NetworkDiscoveryService(settings.scan_subnets)
    protocol_registry = ProtocolRegistry(
        [ModbusAdapter(settings), SnmpAdapter(settings), MqttAdapter(settings), DBusAdapter(), TcpAdapter()]
    )
    return IngestionCoordinator(db, discovery, protocol_registry, rule_engine, semantic_intelligence)
