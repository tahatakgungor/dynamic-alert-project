from pathlib import Path

from dynamic_alert.config import Settings
from dynamic_alert.services.discovery import DiscoveredDevice
from dynamic_alert.services.protocols.modbus import ModbusAdapter
from dynamic_alert.services.protocols.modbus_profiles import ModbusProfileRepository


def test_decode_single_signed_register() -> None:
    assert ModbusAdapter.decode_register_value([0xFFFE], signed=True) == -2


def test_decode_multi_register_value() -> None:
    assert ModbusAdapter.decode_register_value([0x0001, 0x0002], signed=False) == 65538


def test_profile_repository_matches_vendor(tmp_path: Path) -> None:
    profile_file = tmp_path / "profiles.json"
    profile_file.write_text(
        """
        [
          {
            "name": "vendor-profile",
            "vendor": "Generic PLC",
            "metric_key": "temperature_c",
            "register_type": "holding",
            "address": 0,
            "count": 1,
            "unit_id": 1
          }
        ]
        """
    )
    repository = ModbusProfileRepository(str(profile_file))
    device = DiscoveredDevice(
        site_code="HQ-PLANT",
        ip_address="192.168.1.20",
        hostname="press-line-01",
        vendor="Generic PLC",
        open_ports={502},
    )

    assert len(repository.match(device)) == 1


def test_modbus_adapter_uses_profile_repository_path() -> None:
    settings = Settings(modbus_profiles_path="configs/modbus_profiles.json")
    adapter = ModbusAdapter(settings)
    assert adapter.profile_repository.path.name == "modbus_profiles.json"
