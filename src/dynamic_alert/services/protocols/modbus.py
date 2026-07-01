from __future__ import annotations

from typing import Any

from dynamic_alert.config import Settings
from dynamic_alert.services.discovery import DiscoveredDevice
from dynamic_alert.services.protocols.base import FingerprintResult, ProtocolAdapter
from dynamic_alert.services.protocols.modbus_profiles import ModbusProfileRepository, ModbusRegisterProfile


class ModbusAdapter(ProtocolAdapter):
    name = "modbus_tcp"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.profile_repository = ModbusProfileRepository(settings.modbus_profiles_path)

    def matches(self, open_ports: set[int]) -> bool:
        return 502 in open_ports

    def fingerprint(self, ip_address: str, open_ports: set[int]) -> FingerprintResult:
        return FingerprintResult(
            protocol_name=self.name,
            confidence=0.92,
            details=f"{ip_address} cihazinda 502/tcp acik. Modbus/TCP yuksek olasilik.",
        )

    def collect_telemetry(self, device: DiscoveredDevice) -> list[dict]:
        try:
            from pymodbus.client import ModbusTcpClient
        except ImportError:
            return []

        client = ModbusTcpClient(host=device.ip_address, port=502, timeout=self.settings.modbus_timeout_seconds)
        if not client.connect():
            return []

        try:
            profiles = self.profile_repository.match(device, profile_set=self.settings.modbus_profile_set)
            if profiles:
                return self._read_profiles(client, profiles)
            if self.settings.modbus_generic_probe_enabled:
                return self._generic_probe(client)
            return []
        finally:
            client.close()

    def _read_profiles(self, client: Any, profiles: list[ModbusRegisterProfile]) -> list[dict]:
        telemetry: list[dict] = []
        for profile in profiles:
            registers = self._read_registers(
                client,
                register_type=profile.register_type,
                address=profile.address,
                count=profile.count,
                unit_id=profile.unit_id,
            )
            if not registers:
                continue
            value = self.decode_register_value(registers, signed=profile.signed)
            telemetry.append(
                {
                    "metric_key": profile.metric_key,
                    "value": (value * profile.scale) + profile.offset,
                    "unit": profile.unit,
                    "source_protocol": self.name,
                }
            )
        return telemetry

    def _generic_probe(self, client: Any) -> list[dict]:
        telemetry: list[dict] = []
        count = self.settings.modbus_generic_probe_count
        for register_type in ("holding", "input"):
            registers = self._read_registers(client, register_type=register_type, address=0, count=count, unit_id=1)
            if not registers:
                continue
            for index, register in enumerate(registers):
                telemetry.append(
                    {
                        "metric_key": f"modbus_{register_type}_{index}",
                        "value": float(register),
                        "unit": None,
                        "source_protocol": self.name,
                    }
                )
        return telemetry

    def _read_registers(
        self,
        client: Any,
        *,
        register_type: str,
        address: int,
        count: int,
        unit_id: int,
    ) -> list[int]:
        method = client.read_holding_registers if register_type == "holding" else client.read_input_registers
        response = None
        for unit_keyword in ("device_id", "slave", "unit"):
            try:
                response = method(address=address, count=count, **{unit_keyword: unit_id})
                break
            except TypeError:
                continue
            except Exception:
                return []
        if response is None:
            return []
        if hasattr(response, "isError") and response.isError():
            return []
        return list(getattr(response, "registers", []) or [])

    @staticmethod
    def decode_register_value(registers: list[int], *, signed: bool = False) -> int:
        if len(registers) == 1:
            value = registers[0]
            if signed and value >= 0x8000:
                return value - 0x10000
            return value
        value = 0
        for register in registers:
            value = (value << 16) | register
        bit_width = len(registers) * 16
        if signed and value >= (1 << (bit_width - 1)):
            value -= 1 << bit_width
        return value
