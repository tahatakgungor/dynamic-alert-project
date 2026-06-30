from collections.abc import Iterable

from dynamic_alert.services.protocols.base import ProtocolAdapter


class ProtocolRegistry:
    def __init__(self, adapters: Iterable[ProtocolAdapter]) -> None:
        self._adapters = list(adapters)

    def all(self) -> list[ProtocolAdapter]:
        return list(self._adapters)
