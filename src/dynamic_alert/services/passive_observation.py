from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from dynamic_alert.config import Settings
from dynamic_alert.models import Device, FlowCluster, TrafficObservation
from dynamic_alert.services.traffic_intelligence import TrafficIntelligenceService


@dataclass(slots=True)
class PacketSample:
    source_ip: str
    source_port: int
    destination_ip: str
    destination_port: int
    transport: str
    payload_sample: str | None = None


class PassiveObservationService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.traffic_intelligence = TrafficIntelligenceService(db)

    def ingest_samples(self, samples: list[PacketSample]) -> dict[str, int]:
        observation_count = 0
        cluster_count = 0

        for sample in samples:
            device = self.db.query(Device).filter(Device.ip_address == sample.source_ip).one_or_none()
            protocol_hint = self._infer_protocol_hint(sample)
            observation = TrafficObservation(
                device_id=device.id if device else None,
                source_ip=sample.source_ip,
                source_port=sample.source_port,
                destination_ip=sample.destination_ip,
                destination_port=sample.destination_port,
                transport=sample.transport,
                protocol_hint=protocol_hint,
                payload_sample=sample.payload_sample,
                direction="outbound",
                observed_at=datetime.utcnow(),
            )
            self.db.add(observation)
            observation_count += 1

            cluster_key = self._build_cluster_key(sample)
            cluster = self.db.query(FlowCluster).filter(FlowCluster.cluster_key == cluster_key).one_or_none()
            if cluster is None:
                cluster = FlowCluster(
                    cluster_key=cluster_key,
                    protocol_hint=protocol_hint,
                    source_ip=sample.source_ip,
                    destination_ip=sample.destination_ip,
                    destination_port=sample.destination_port,
                    transport=sample.transport,
                    sample_count=1,
                    last_payload_sample=sample.payload_sample,
                    updated_at=datetime.utcnow(),
                )
                self.db.add(cluster)
                cluster_count += 1
            else:
                cluster.protocol_hint = protocol_hint
                cluster.sample_count += 1
                cluster.last_payload_sample = sample.payload_sample
                cluster.updated_at = datetime.utcnow()

            self.db.flush()
            self.traffic_intelligence.refresh_candidates_for_cluster(cluster)

        self.db.commit()
        return {"observations": observation_count, "new_clusters": cluster_count}

    def capture_live_samples(self) -> list[PacketSample]:
        try:
            from scapy.all import IP, Raw, TCP, UDP, sniff
        except ImportError:
            return []

        packets = sniff(
            iface=self.settings.packet_capture_interface or None,
            timeout=self.settings.packet_capture_timeout_seconds,
            count=self.settings.packet_capture_max_packets,
            filter=self.settings.packet_capture_bpf_filter,
            store=True,
        )

        samples: list[PacketSample] = []
        for packet in packets:
            if IP not in packet:
                continue
            sample = self._packet_to_sample(packet, ip_cls=IP, tcp_cls=TCP, udp_cls=UDP, raw_cls=Raw)
            if sample is not None:
                samples.append(sample)
        return samples

    @staticmethod
    def _packet_to_sample(
        packet: Any,
        *,
        ip_cls: Any,
        tcp_cls: Any,
        udp_cls: Any,
        raw_cls: Any,
    ) -> PacketSample | None:
        if ip_cls not in packet:
            return None

        ip_layer = packet[ip_cls]
        if tcp_cls in packet:
            transport = "tcp"
            source_port = int(packet[tcp_cls].sport)
            destination_port = int(packet[tcp_cls].dport)
        elif udp_cls in packet:
            transport = "udp"
            source_port = int(packet[udp_cls].sport)
            destination_port = int(packet[udp_cls].dport)
        else:
            return None

        payload_sample = None
        if raw_cls in packet:
            payload_sample = bytes(packet[raw_cls].load[:64]).hex()

        return PacketSample(
            source_ip=str(ip_layer.src),
            source_port=source_port,
            destination_ip=str(ip_layer.dst),
            destination_port=destination_port,
            transport=transport,
            payload_sample=payload_sample,
        )

    @staticmethod
    def _build_cluster_key(sample: PacketSample) -> str:
        return f"{sample.transport}:{sample.source_ip}:{sample.destination_ip}:{sample.destination_port}"

    @staticmethod
    def _infer_protocol_hint(sample: PacketSample) -> str:
        if sample.destination_port == 502:
            return "modbus_tcp"
        if sample.destination_port == 1883:
            return "mqtt"
        if sample.destination_port == 161:
            return "snmp"
        if sample.destination_port == 4840:
            return "opc_ua"
        return "unknown"

    def sample_demo_traffic(self) -> list[PacketSample]:
        return [
            PacketSample(
                source_ip="192.168.1.20",
                source_port=41421,
                destination_ip="192.168.1.100",
                destination_port=502,
                transport="tcp",
                payload_sample="010300000002",
            ),
            PacketSample(
                source_ip="192.168.1.21",
                source_port=49812,
                destination_ip="192.168.1.101",
                destination_port=1883,
                transport="tcp",
                payload_sample="factory/line1/temp 42.1",
            ),
        ]
