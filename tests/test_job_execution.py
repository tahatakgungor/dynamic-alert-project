from dynamic_alert.config import Settings
from dynamic_alert.services.job_execution import apply_settings_overrides


def test_apply_settings_overrides_updates_scan_and_capture_fields() -> None:
    settings = Settings()

    updated = apply_settings_overrides(
        settings,
        {
            "scan_subnets": ["10.20.30.0/24", "10.20.31.0/24"],
            "packet_capture_interface": "eth1",
            "packet_capture_timeout_seconds": 9,
            "packet_capture_max_packets": 55,
            "packet_capture_bpf_filter": "tcp port 502",
            "packet_capture_include_link_local": True,
            "modbus_generic_probe_count": 8,
            "modbus_profile_set": "generic_plc",
            "modbus_profiles_path": "configs/custom_modbus_profiles.json",
            "mqtt_topic_set": "factory_default",
            "mqtt_probe_topics": ["factory/telemetry/#", "alerts/#"],
            "mqtt_probe_max_messages": 6,
            "snmp_oid_set": "standard_mib2",
            "snmp_oid_sysname": "1.3.6.1.2.1.1.5.0",
            "opcua_max_nodes": 20,
        },
    )

    assert updated.scan_subnets == ["10.20.30.0/24", "10.20.31.0/24"]
    assert updated.packet_capture_interface == "eth1"
    assert updated.packet_capture_timeout_seconds == 9
    assert updated.packet_capture_max_packets == 55
    assert updated.packet_capture_bpf_filter == "tcp port 502"
    assert updated.packet_capture_include_link_local is True
    assert updated.modbus_generic_probe_count == 8
    assert updated.modbus_profile_set == "generic_plc"
    assert updated.modbus_profiles_path == "configs/custom_modbus_profiles.json"
    assert updated.mqtt_topic_set == "factory_default"
    assert updated.mqtt_probe_topics == ["factory/telemetry/#", "alerts/#"]
    assert updated.mqtt_probe_max_messages == 6
    assert updated.snmp_oid_set == "standard_mib2"
    assert updated.snmp_oid_sysname == "1.3.6.1.2.1.1.5.0"
    assert updated.opcua_max_nodes == 20
