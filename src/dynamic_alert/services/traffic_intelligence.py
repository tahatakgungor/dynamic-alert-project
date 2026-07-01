from __future__ import annotations

from datetime import datetime
import re

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
        elif self._is_operator_locked(candidate.status):
            candidate.updated_at = datetime.utcnow()
        else:
            candidate.candidate_label = label
            candidate.confidence = confidence
            candidate.evidence = evidence
            candidate.payload_fingerprint = fingerprint
            candidate.status = status
            candidate.updated_at = datetime.utcnow()

        return candidate

    def apply_candidate_action(
        self,
        *,
        candidate_id: int,
        action: str,
        candidate_label: str | None = None,
        notes: str | None = None,
    ) -> UnknownProtocolCandidate:
        candidate = (
            self.db.query(UnknownProtocolCandidate)
            .filter(UnknownProtocolCandidate.id == candidate_id)
            .one()
        )
        normalized_action = action.strip().lower()
        if normalized_action not in {"confirm", "dismiss", "escalate"}:
            raise ValueError(f"unsupported action: {action}")

        if normalized_action == "confirm":
            candidate.status = "confirmed"
            if candidate_label:
                candidate.candidate_label = candidate_label
            candidate.confidence = 1.0
        elif normalized_action == "dismiss":
            candidate.status = "dismissed"
            candidate.confidence = 0.0
        else:
            candidate.status = "escalated"
            candidate.confidence = max(candidate.confidence, 0.85)
            if candidate_label:
                candidate.candidate_label = candidate_label

        if notes:
            candidate.evidence = f"{candidate.evidence} | operator_note={notes}"
        candidate.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def _infer_candidate(self, cluster: FlowCluster) -> tuple[str, float, str, str | None, str]:
        raw_payload = cluster.last_payload_sample or ""
        payload = raw_payload.lower()
        fingerprint = self._payload_fingerprint(cluster.last_payload_sample)
        evidence_parts = [
            f"transport={cluster.transport}",
            f"destination_port={cluster.destination_port}",
            f"sample_count={cluster.sample_count}",
        ]

        if cluster.protocol_hint != "unknown":
            return (
                cluster.protocol_hint,
                0.9,
                f"{', '.join(evidence_parts)}, matched known protocol hint",
                fingerprint,
                "known-hint",
            )

        if self._looks_like_modbus_request(payload):
            evidence_parts.append("payload_pattern=register_request_like")
            return ("possible_modbus_variant", 0.66, ", ".join(evidence_parts), fingerprint, "candidate")

        if self._looks_like_mqtt_plaintext(raw_payload):
            evidence_parts.append("payload_pattern=topic_value_plaintext")
            return ("possible_mqtt_like_plaintext", 0.62, ", ".join(evidence_parts), fingerprint, "candidate")

        port_label = self._industrial_port_candidate(cluster.destination_port)
        if port_label is not None:
            evidence_parts.append("port_profile=industrial_common")
            return (
                port_label,
                self._base_confidence_for_port(cluster.destination_port, cluster.sample_count),
                ", ".join(evidence_parts),
                fingerprint,
                "candidate",
            )

        return (
            "unknown_binary_flow",
            0.35,
            ", ".join(evidence_parts),
            fingerprint,
            "candidate",
        )

    @staticmethod
    def _payload_fingerprint(payload_sample: str | None) -> str | None:
        if not payload_sample:
            return None
        return payload_sample[:24]

    @staticmethod
    def _looks_like_modbus_request(payload: str) -> bool:
        return payload.startswith("0103") or payload.startswith("0001")

    @staticmethod
    def _looks_like_mqtt_plaintext(payload: str) -> bool:
        lowered = payload.lower()
        if "/" not in lowered:
            return False
        if not re.search(r"\b\d+(?:\.\d+)?\b", lowered):
            return False
        return any(token in lowered for token in ("temp", "temperature", "factory", "line", "sensor"))

    @staticmethod
    def _industrial_port_candidate(destination_port: int) -> str | None:
        if destination_port == 102:
            return "possible_s7comm_flow"
        if destination_port == 44818:
            return "possible_ethernet_ip_flow"
        if destination_port == 20000:
            return "industrial_unknown_high_priority"
        return None

    @staticmethod
    def _base_confidence_for_port(destination_port: int, sample_count: int) -> float:
        base = {
            102: 0.64,
            44818: 0.64,
            20000: 0.58,
        }.get(destination_port, 0.5)
        if sample_count >= 10:
            return min(base + 0.08, 0.9)
        if sample_count >= 5:
            return min(base + 0.04, 0.9)
        return base

    @staticmethod
    def _is_operator_locked(status: str) -> bool:
        return status in {"confirmed", "dismissed", "escalated"}
