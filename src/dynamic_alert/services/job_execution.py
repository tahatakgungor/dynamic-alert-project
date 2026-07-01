from __future__ import annotations

from typing import Any

from dynamic_alert.config import Settings
from dynamic_alert.services.discovery import DiscoveredDevice
from dynamic_alert.services.ingestion import IngestionCoordinator
from dynamic_alert.services.passive_observation import PacketSample, PassiveObservationService


def apply_settings_overrides(settings: Settings, payload: dict[str, Any] | None) -> Settings:
    if not payload:
        return settings

    updates: dict[str, Any] = {}
    if "scan_subnets" in payload and isinstance(payload["scan_subnets"], list):
        updates["scan_subnets_raw"] = ",".join(str(item) for item in payload["scan_subnets"] if str(item).strip())
    if "packet_capture_interface" in payload:
        updates["packet_capture_interface"] = payload["packet_capture_interface"]
    if "packet_capture_timeout_seconds" in payload:
        updates["packet_capture_timeout_seconds"] = float(payload["packet_capture_timeout_seconds"])
    if "packet_capture_max_packets" in payload:
        updates["packet_capture_max_packets"] = int(payload["packet_capture_max_packets"])
    if "packet_capture_bpf_filter" in payload:
        updates["packet_capture_bpf_filter"] = payload["packet_capture_bpf_filter"]
    if "packet_capture_include_link_local" in payload:
        updates["packet_capture_include_link_local"] = bool(payload["packet_capture_include_link_local"])
    if "modbus_generic_probe_enabled" in payload:
        updates["modbus_generic_probe_enabled"] = bool(payload["modbus_generic_probe_enabled"])
    if "modbus_generic_probe_count" in payload:
        updates["modbus_generic_probe_count"] = max(1, min(int(payload["modbus_generic_probe_count"]), 32))
    if "modbus_timeout_seconds" in payload:
        updates["modbus_timeout_seconds"] = max(0.1, min(float(payload["modbus_timeout_seconds"]), 10.0))
    if "modbus_profiles_path" in payload and payload["modbus_profiles_path"]:
        updates["modbus_profiles_path"] = str(payload["modbus_profiles_path"])
    if "modbus_profile_set" in payload and payload["modbus_profile_set"]:
        updates["modbus_profile_set"] = str(payload["modbus_profile_set"])
    if "mqtt_topic_set" in payload and payload["mqtt_topic_set"]:
        updates["mqtt_topic_set"] = str(payload["mqtt_topic_set"])
    if "mqtt_probe_topics" in payload and isinstance(payload["mqtt_probe_topics"], list):
        updates["mqtt_probe_topics_raw"] = ",".join(str(item) for item in payload["mqtt_probe_topics"] if str(item).strip())
    if "mqtt_probe_timeout_seconds" in payload:
        updates["mqtt_probe_timeout_seconds"] = max(0.1, min(float(payload["mqtt_probe_timeout_seconds"]), 15.0))
    if "mqtt_probe_max_messages" in payload:
        updates["mqtt_probe_max_messages"] = max(1, min(int(payload["mqtt_probe_max_messages"]), 20))
    if "snmp_timeout_seconds" in payload:
        updates["snmp_timeout_seconds"] = max(0.1, min(float(payload["snmp_timeout_seconds"]), 10.0))
    if "snmp_oid_set" in payload and payload["snmp_oid_set"]:
        updates["snmp_oid_set"] = str(payload["snmp_oid_set"])
    if "snmp_oid_sysdescr" in payload and payload["snmp_oid_sysdescr"]:
        updates["snmp_oid_sysdescr"] = str(payload["snmp_oid_sysdescr"])
    if "snmp_oid_sysname" in payload and payload["snmp_oid_sysname"]:
        updates["snmp_oid_sysname"] = str(payload["snmp_oid_sysname"])
    if "snmp_oid_uptime" in payload and payload["snmp_oid_uptime"]:
        updates["snmp_oid_uptime"] = str(payload["snmp_oid_uptime"])
    if "opcua_timeout_seconds" in payload:
        updates["opcua_timeout_seconds"] = max(0.1, min(float(payload["opcua_timeout_seconds"]), 15.0))
    if "opcua_max_nodes" in payload:
        updates["opcua_max_nodes"] = max(1, min(int(payload["opcua_max_nodes"]), 64))

    return settings.model_copy(update=updates)


def execute_scan(coordinator: IngestionCoordinator) -> dict[str, int]:
    return coordinator.run_cycle()


def execute_passive_observe(service: PassiveObservationService, payload: dict[str, Any] | None = None) -> dict[str, int]:
    if payload and isinstance(payload.get("samples"), list):
        samples = [_sample_from_payload(item) for item in payload["samples"]]
        return service.ingest_samples([item for item in samples if item is not None])
    return service.ingest_samples(service.sample_demo_traffic())


def execute_live_capture(service: PassiveObservationService) -> dict[str, int]:
    samples = service.capture_live_samples()
    return service.ingest_samples(samples)


def execute_dbus_demo(coordinator: IngestionCoordinator, payload: dict[str, Any] | None = None) -> dict[str, int]:
    payload = payload or {}
    open_ports = payload.get("open_ports")
    normalized_ports = {int(port) for port in open_ports} if isinstance(open_ports, list) and open_ports else {22, 80}
    return coordinator.ingest_device(
        DiscoveredDevice(
            site_code=str(payload.get("site_code") or "HQ-PLANT"),
            ip_address=str(payload.get("ip_address") or "192.168.1.250"),
            hostname=str(payload.get("hostname") or "dbus-temp-gateway-demo"),
            vendor=str(payload.get("vendor") or "Linux Edge Gateway"),
            open_ports=normalized_ports,
        )
    )


def _sample_from_payload(value: Any) -> PacketSample | None:
    if not isinstance(value, dict):
        return None
    return PacketSample(
        source_ip=str(value.get("source_ip", "")),
        source_port=int(value.get("source_port", 0)),
        destination_ip=str(value.get("destination_ip", "")),
        destination_port=int(value.get("destination_port", 0)),
        transport=str(value.get("transport", "tcp")),
        payload_sample=str(value["payload_sample"]) if value.get("payload_sample") is not None else None,
    )
