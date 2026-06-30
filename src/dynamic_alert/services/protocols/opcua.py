from __future__ import annotations

import asyncio
from numbers import Number

from dynamic_alert.config import Settings
from dynamic_alert.services.discovery import DiscoveredDevice
from dynamic_alert.services.protocols.base import FingerprintResult, ProtocolAdapter


class OpcUaAdapter(ProtocolAdapter):
    name = "opc_ua"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def matches(self, open_ports: set[int]) -> bool:
        return 4840 in open_ports

    def fingerprint(self, ip_address: str, open_ports: set[int]) -> FingerprintResult:
        return FingerprintResult(
            protocol_name=self.name,
            confidence=0.86,
            details=f"{ip_address} cihazinda 4840/tcp acik. OPC UA endpoint olabilir.",
        )

    def collect_telemetry(self, device: DiscoveredDevice) -> list[dict]:
        try:
            return asyncio.run(self._collect(device))
        except Exception:
            return []

    async def _collect(self, device: DiscoveredDevice) -> list[dict]:
        try:
            from asyncua import Client
            from asyncua.ua import NodeClass
        except ImportError:
            return []

        telemetry: list[dict] = []
        url = f"opc.tcp://{device.ip_address}:4840"
        client = Client(url=url, timeout=self.settings.opcua_timeout_seconds)

        async with client:
            objects = client.nodes.objects
            children = await objects.get_children()
            visited = 0

            for node in children:
                if visited >= self.settings.opcua_max_nodes:
                    break
                visited += 1
                telemetry.extend(await self._extract_node_values(node, NodeClass))
                if len(telemetry) >= self.settings.opcua_max_nodes:
                    break
        return telemetry[: self.settings.opcua_max_nodes]

    async def _extract_node_values(self, node, node_class_enum) -> list[dict]:
        telemetry: list[dict] = []
        try:
            node_class = await node.read_node_class()
            browse_name = await node.read_browse_name()
        except Exception:
            return telemetry

        if node_class == node_class_enum.Variable:
            try:
                value = await node.read_value()
            except Exception:
                return telemetry
            if isinstance(value, Number):
                telemetry.append(
                    {
                        "metric_key": f"opcua_{browse_name.Name}".lower(),
                        "value": float(value),
                        "unit": None,
                        "source_protocol": self.name,
                    }
                )
            return telemetry

        try:
            children = await node.get_children()
        except Exception:
            return telemetry

        for child in children[:4]:
            telemetry.extend(await self._extract_node_values(child, node_class_enum))
        return telemetry
