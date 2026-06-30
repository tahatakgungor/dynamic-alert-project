from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from dynamic_alert.models import Device, FlowCluster, TrafficObservation


@dataclass(slots=True)
class PacketSample:
    source_ip: str
    source_port: int
    destination_ip: str
    destination_port: int
    transport: str
    payload_sample: str | None = None


class PassiveObservationService:
    def __init__(self, db: Session) -> None:
        self.db = db

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

        self.db.commit()
        return {"observations": observation_count, "new_clusters": cluster_count}

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
