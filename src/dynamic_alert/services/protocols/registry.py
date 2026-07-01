from collections.abc import Iterable

from dynamic_alert.services.protocols.base import ProtocolAdapter


class ProtocolRegistry:
    def __init__(self, adapters: Iterable[ProtocolAdapter]) -> None:
        self._adapters = list(adapters)

    def all(self) -> list[ProtocolAdapter]:
        return list(self._adapters)

    def names(self) -> list[str]:
        return [adapter.name for adapter in self._adapters]

    def select(self, names: list[str] | None) -> "ProtocolRegistry":
        if not names:
            return ProtocolRegistry(self._adapters)
        allowed = set(names)
        return ProtocolRegistry([adapter for adapter in self._adapters if adapter.name in allowed])
