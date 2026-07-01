from dynamic_alert.config import Settings
from dynamic_alert.services.protocols.mqtt import MqttAdapter
from dynamic_alert.services.protocols.mqtt_topics import MqttTopicRepository
from dynamic_alert.services.protocols.snmp import SnmpAdapter
from dynamic_alert.services.protocols.snmp_oids import SnmpOidRepository


def test_mqtt_numeric_extraction_prefers_number() -> None:
    assert MqttAdapter._extract_numeric("temperature 42.5 C") == 42.5


def test_mqtt_numeric_extraction_falls_back_to_length() -> None:
    assert MqttAdapter._extract_numeric("alarm-active") == float(len("alarm-active"))


def test_snmp_numeric_coercion_falls_back_to_length() -> None:
    assert SnmpAdapter._coerce_numeric("edge-gateway") == float(len("edge-gateway"))


def test_settings_parse_mqtt_probe_topics() -> None:
    settings = Settings(mqtt_probe_topics_raw="factory/telemetry/#,alerts/#")
    assert settings.mqtt_probe_topics == ["factory/telemetry/#", "alerts/#"]


def test_mqtt_topic_repository_supports_named_sets(tmp_path) -> None:
    topic_file = tmp_path / "mqtt_topics.json"
    topic_file.write_text(
        """
        {
          "default_set": "factory_default",
          "topic_sets": {
            "factory_default": ["factory/telemetry/#", "alerts/#"],
            "packaging_line": ["factory/packaging/#"]
          }
        }
        """
    )

    repository = MqttTopicRepository(str(topic_file))

    assert repository.topic_sets() == ["factory_default", "packaging_line"]
    assert repository.resolve("packaging_line") == ["factory/packaging/#"]


def test_snmp_oid_repository_supports_named_sets(tmp_path) -> None:
    oid_file = tmp_path / "snmp_oids.json"
    oid_file.write_text(
        """
        {
          "default_set": "standard_mib2",
          "oid_sets": {
            "standard_mib2": {
              "snmp_oid_sysdescr": "1.3.6.1.2.1.1.1.0",
              "snmp_oid_sysname": "1.3.6.1.2.1.1.5.0",
              "snmp_oid_uptime": "1.3.6.1.2.1.1.3.0"
            },
            "identity_only": {
              "snmp_oid_sysdescr": "1.3.6.1.2.1.1.1.0",
              "snmp_oid_sysname": "1.3.6.1.2.1.1.5.0"
            }
          }
        }
        """
    )

    repository = SnmpOidRepository(str(oid_file))

    assert repository.oid_sets() == ["standard_mib2", "identity_only"]
    assert repository.resolve("identity_only") == {
        "snmp_oid_sysdescr": "1.3.6.1.2.1.1.1.0",
        "snmp_oid_sysname": "1.3.6.1.2.1.1.5.0",
    }
