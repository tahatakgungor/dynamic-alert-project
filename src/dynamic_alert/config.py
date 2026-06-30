from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DYNAMIC_ALERT_", extra="ignore")

    app_name: str = "Dynamic Alert"
    env: str = "development"
    database_url: str = "sqlite:///./dynamic_alert.db"
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    scan_subnets_raw: str = "192.168.1.0/24"
    api_cors_origins_raw: str = "http://127.0.0.1:8000,http://localhost:8000"
    bootstrap_api_key: str = "change-me-before-production"
    local_ai_enabled: bool = True
    local_ai_model_name: str = "semantic-heuristic-v1"
    local_ai_online_learning_enabled: bool = True
    modbus_profiles_path: str = "configs/modbus_profiles.json"
    modbus_timeout_seconds: float = 1.0
    modbus_generic_probe_enabled: bool = True
    modbus_generic_probe_count: int = 4
    mqtt_probe_topics_raw: str = "#"
    mqtt_probe_timeout_seconds: float = 2.0
    mqtt_probe_max_messages: int = 3
    snmp_community: str = "public"
    snmp_timeout_seconds: float = 1.0
    snmp_port: int = 161
    snmp_oid_sysdescr: str = "1.3.6.1.2.1.1.1.0"
    snmp_oid_sysname: str = "1.3.6.1.2.1.1.5.0"
    snmp_oid_uptime: str = "1.3.6.1.2.1.1.3.0"
    packet_capture_interface: str | None = None
    packet_capture_timeout_seconds: float = 5.0
    packet_capture_max_packets: int = 100
    packet_capture_bpf_filter: str = "tcp or udp"
    opcua_timeout_seconds: float = 2.0
    opcua_max_nodes: int = 12

    @computed_field
    @property
    def scan_subnets(self) -> list[str]:
        return [item.strip() for item in self.scan_subnets_raw.split(",") if item.strip()]

    @computed_field
    @property
    def api_cors_origins(self) -> list[str]:
        return [item.strip() for item in self.api_cors_origins_raw.split(",") if item.strip()]

    @computed_field
    @property
    def mqtt_probe_topics(self) -> list[str]:
        return [item.strip() for item in self.mqtt_probe_topics_raw.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
