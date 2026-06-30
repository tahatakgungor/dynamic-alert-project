from dynamic_alert.services.protocols.base import FingerprintResult, ProtocolAdapter


class DBusAdapter(ProtocolAdapter):
    name = "dbus_gateway"

    def matches(self, open_ports: set[int]) -> bool:
        return 22 in open_ports and 80 in open_ports

    def fingerprint(self, ip_address: str, open_ports: set[int]) -> FingerprintResult:
        return FingerprintResult(
            protocol_name=self.name,
            confidence=0.40,
            details=f"{ip_address} Linux tabanli bir gateway olabilir; D-Bus yerel entegrasyon icin aday.",
        )
