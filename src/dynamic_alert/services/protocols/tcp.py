from dynamic_alert.services.protocols.base import FingerprintResult, ProtocolAdapter


class TcpAdapter(ProtocolAdapter):
    name = "raw_tcp"

    def matches(self, open_ports: set[int]) -> bool:
        return bool(open_ports)

    def fingerprint(self, ip_address: str, open_ports: set[int]) -> FingerprintResult:
        ports = ",".join(str(port) for port in sorted(open_ports))
        return FingerprintResult(
            protocol_name=self.name,
            confidence=0.35,
            details=f"{ip_address} icin acik portlar: {ports}. Bilinen bir application protocol'u net degil.",
        )
