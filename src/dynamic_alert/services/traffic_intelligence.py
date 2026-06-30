from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from dynamic_alert.models import FlowCluster, UnknownProtocolCandidate


class TrafficIntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def refresh_candidates_for_cluster(self, cluster: FlowCluster) -> UnknownProtocolCandidate | None:
        candidate = (
            self.db.query(UnknownProtocolCandidate)
            .filter(UnknownProtocolCandidate.flow_cluster_id == cluster.id)
            .one_or_none()
        )
        label, confidence, evidence, fingerprint, status = self._infer_candidate(cluster)

        if candidate is None:
            candidate = UnknownProtocolCandidate(
                flow_cluster_id=cluster.id,
                candidate_label=label,
                confidence=confidence,
                evidence=evidence,
                payload_fingerprint=fingerprint,
                status=status,
                updated_at=datetime.utcnow(),
            )
            self.db.add(candidate)
        else:
            candidate.candidate_label = label
            candidate.confidence = confidence
            candidate.evidence = evidence
            candidate.payload_fingerprint = fingerprint
            candidate.status = status
            candidate.updated_at = datetime.utcnow()

        return candidate

    def _infer_candidate(self, cluster: FlowCluster) -> tuple[str, float, str, str | None, str]:
        payload = (cluster.last_payload_sample or "").lower()
        fingerprint = self._payload_fingerprint(cluster.last_payload_sample)

        if cluster.protocol_hint != "unknown":
            return (
                cluster.protocol_hint,
                0.9,
                f"destination_port={cluster.destination_port} matched known protocol hint",
                fingerprint,
                "known-hint",
            )
        if payload.startswith("0103") or payload.startswith("0001"):
            return ("possible_modbus_variant", 0.66, "payload fingerprint resembles register request", fingerprint, "candidate")
        if "temp" in payload or "factory" in payload:
            return ("possible_mqtt_like_plaintext", 0.62, "payload contains topic/value style plaintext", fingerprint, "candidate")
        if cluster.destination_port in {20000, 44818, 102}:
            return (
                "industrial_unknown_high_priority",
                0.58,
                f"destination_port={cluster.destination_port} is common in industrial contexts",
                fingerprint,
                "candidate",
            )
        return (
            "unknown_binary_flow",
            0.35,
            f"transport={cluster.transport}, port={cluster.destination_port}, sample_count={cluster.sample_count}",
            fingerprint,
            "candidate",
        )

    @staticmethod
    def _payload_fingerprint(payload_sample: str | None) -> str | None:
        if not payload_sample:
            return None
        return payload_sample[:24]
