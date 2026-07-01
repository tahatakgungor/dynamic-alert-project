from dynamic_alert.config import Settings
from dynamic_alert.services.container import create_protocol_registry


def test_create_protocol_registry_filters_enabled_protocols() -> None:
    registry = create_protocol_registry(Settings(), enabled_protocol_names=["mqtt", "opc_ua"])

    assert registry.names() == ["mqtt", "opc_ua"]
