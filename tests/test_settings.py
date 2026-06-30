from dynamic_alert.config import Settings


def test_settings_parse_csv_fields() -> None:
    settings = Settings(
        scan_subnets_raw="192.168.1.0/24,10.0.0.0/24",
        api_cors_origins_raw="http://localhost:3000,http://127.0.0.1:8000",
    )

    assert settings.scan_subnets == ["192.168.1.0/24", "10.0.0.0/24"]
    assert settings.api_cors_origins == ["http://localhost:3000", "http://127.0.0.1:8000"]
