from dynamic_alert.config import Settings
from dynamic_alert.services.protocols.mqtt import MqttAdapter
from dynamic_alert.services.protocols.snmp import SnmpAdapter


def test_mqtt_numeric_extraction_prefers_number() -> None:
    assert MqttAdapter._extract_numeric("temperature 42.5 C") == 42.5


def test_mqtt_numeric_extraction_falls_back_to_length() -> None:
    assert MqttAdapter._extract_numeric("alarm-active") == float(len("alarm-active"))


def test_snmp_numeric_coercion_falls_back_to_length() -> None:
    assert SnmpAdapter._coerce_numeric("edge-gateway") == float(len("edge-gateway"))


def test_settings_parse_mqtt_probe_topics() -> None:
    settings = Settings(mqtt_probe_topics_raw="factory/telemetry/#,alerts/#")
    assert settings.mqtt_probe_topics == ["factory/telemetry/#", "alerts/#"]
