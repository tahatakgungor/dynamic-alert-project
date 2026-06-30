from dataclasses import dataclass


@dataclass(slots=True)
class DiscoveredDevice:
    ip_address: str
    hostname: str | None
    vendor: str | None
    open_ports: set[int]


class NetworkDiscoveryService:
    def __init__(self, subnets: list[str]) -> None:
        self.subnets = subnets

    def scan(self) -> list[DiscoveredDevice]:
        # Ilk surumde guvenli bir demonstrasyon taramasi donuyoruz.
        # Gercek sahada bu katman ARP/ICMP/TCP fingerprinting ile degisecek.
        return [
            DiscoveredDevice(
                ip_address="192.168.1.20",
                hostname="press-line-01",
                vendor="Generic PLC",
                open_ports={502},
            ),
            DiscoveredDevice(
                ip_address="192.168.1.21",
                hostname="edge-gateway-01",
                vendor="Industrial IPC",
                open_ports={22, 80},
            ),
        ]
