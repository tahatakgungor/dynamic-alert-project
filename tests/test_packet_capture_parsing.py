from dynamic_alert.services.passive_observation import PassiveObservationService


class FakeIPLayer:
    def __init__(self, src: str, dst: str) -> None:
        self.src = src
        self.dst = dst


class FakePortLayer:
    def __init__(self, sport: int, dport: int) -> None:
        self.sport = sport
        self.dport = dport


class FakeRawLayer:
    def __init__(self, payload: bytes) -> None:
        self.load = payload


class FakePacket:
    def __init__(self, layers: dict[type, object]) -> None:
        self.layers = layers

    def __contains__(self, item: type) -> bool:
        return item in self.layers

    def __getitem__(self, item: type) -> object:
        return self.layers[item]


class IP:
    pass


class TCP:
    pass


class UDP:
    pass


class RAW:
    pass


def test_packet_to_sample_parses_tcp_payload() -> None:
    packet = FakePacket(
        {
            IP: FakeIPLayer("192.168.1.20", "192.168.1.100"),
            TCP: FakePortLayer(40001, 502),
            RAW: FakeRawLayer(b"\x01\x03\x00\x00\x00\x02"),
        }
    )

    sample = PassiveObservationService._packet_to_sample(
        packet,
        ip_cls=IP,
        tcp_cls=TCP,
        udp_cls=UDP,
        raw_cls=RAW,
    )

    assert sample is not None
    assert sample.source_ip == "192.168.1.20"
    assert sample.destination_port == 502
    assert sample.transport == "tcp"
    assert sample.payload_sample == "010300000002"
