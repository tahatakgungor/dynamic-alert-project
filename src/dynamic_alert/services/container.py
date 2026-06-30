from sqlalchemy.orm import Session

from dynamic_alert.config import get_settings
from dynamic_alert.services.discovery import NetworkDiscoveryService
from dynamic_alert.services.ingestion import IngestionCoordinator
from dynamic_alert.services.protocols.dbus import DBusAdapter
from dynamic_alert.services.protocols.modbus import ModbusAdapter
from dynamic_alert.services.protocols.registry import ProtocolRegistry
from dynamic_alert.services.protocols.tcp import TcpAdapter
from dynamic_alert.services.rule_engine import RuleEngine
from dynamic_alert.services.telegram import TelegramNotifier


def get_ingestion_coordinator(db: Session) -> IngestionCoordinator:
    settings = get_settings()
    notifier = TelegramNotifier(settings)
    rule_engine = RuleEngine(db, notifier)
    discovery = NetworkDiscoveryService(settings.scan_subnets)
    protocol_registry = ProtocolRegistry([ModbusAdapter(), DBusAdapter(), TcpAdapter()])
    return IngestionCoordinator(db, discovery, protocol_registry, rule_engine)
