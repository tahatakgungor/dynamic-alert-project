from dataclasses import dataclass


@dataclass(slots=True)
class DiscoveredDevice:
    site_code: str
    ip_address: str
    hostname: str | None
    vendor: str | None
    open_ports: set[int]


class NetworkDiscoveryService:
    def __init__(self, subnets: list[str]) -> None:
        self.subnets = subnets

    def scan(self) -> list[DiscoveredDevice]:
        # Ilk surumde guvenli demonstrasyon cihazlari donuyoruz.
        # Gercek sahada bu katman ARP/ICMP/TCP fingerprinting ile degisecek.
        devices: list[DiscoveredDevice] = []
        for subnet in self.subnets or ["192.168.1.0/24"]:
            prefix = self._subnet_prefix(subnet)
            devices.extend(
                [
                    DiscoveredDevice(
                        site_code="HQ-PLANT",
                        ip_address=f"{prefix}.20",
                        hostname="press-line-01",
                        vendor="Generic PLC",
                        open_ports={502},
                    ),
                    DiscoveredDevice(
                        site_code="HQ-PLANT",
                        ip_address=f"{prefix}.21",
                        hostname="edge-gateway-01",
                        vendor="Industrial IPC",
                        open_ports={22, 80, 1883, 161, 4840},
                    ),
                ]
            )
        return devices

    @staticmethod
    def _subnet_prefix(subnet: str) -> str:
        base = subnet.split("/", 1)[0]
        octets = base.split(".")
        if len(octets) != 4:
            return "192.168.1"
        return ".".join(octets[:3])
