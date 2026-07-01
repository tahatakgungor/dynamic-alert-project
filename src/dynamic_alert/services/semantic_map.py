from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from dynamic_alert.models import Device, SemanticHypothesis, SemanticMap, TelemetryRecord


class SemanticMapService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def resolve_for_telemetry(self, telemetry: TelemetryRecord) -> SemanticMap | None:
        device = self.db.query(Device).filter(Device.id == telemetry.device_id).one_or_none()

        if device is not None:
            mapped = (
                self.db.query(SemanticMap)
                .filter(
                    SemanticMap.scope == "device",
                    SemanticMap.device_id == device.id,
                    SemanticMap.protocol_name == telemetry.source_protocol,
                    SemanticMap.source_key == telemetry.metric_key,
                )
                .one_or_none()
            )
            if mapped is not None:
                return mapped

        vendor = device.vendor if device is not None else None
        return (
            self.db.query(SemanticMap)
            .filter(
                SemanticMap.scope == "vendor",
                SemanticMap.vendor == vendor,
                SemanticMap.protocol_name == telemetry.source_protocol,
                SemanticMap.source_key == telemetry.metric_key,
            )
            .one_or_none()
        )

    def upsert_operator_map(
        self,
        *,
        scope: str,
        device_id: int | None,
        vendor: str | None,
        protocol_name: str,
        source_key: str,
        metric_key: str,
        unit: str | None,
        notes: str | None = None,
    ) -> SemanticMap:
        mapped = (
            self.db.query(SemanticMap)
            .filter(
                SemanticMap.scope == scope,
                SemanticMap.device_id == device_id,
                SemanticMap.vendor == vendor,
                SemanticMap.protocol_name == protocol_name,
                SemanticMap.source_key == source_key,
            )
            .one_or_none()
        )

        if mapped is None:
            mapped = SemanticMap(
                scope=scope,
                device_id=device_id,
                vendor=vendor,
                protocol_name=protocol_name,
                source_key=source_key,
                metric_key=metric_key,
                unit=unit,
                confidence=1.0,
                source_kind="operator-confirmed",
                notes=notes,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(mapped)
        else:
            mapped.metric_key = metric_key
            mapped.unit = unit
            mapped.confidence = 1.0
            mapped.source_kind = "operator-confirmed"
            mapped.notes = notes
            mapped.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(mapped)
        return mapped

    def promote_hypothesis(
        self,
        *,
        hypothesis_id: int,
        scope: str,
        metric_key: str | None = None,
        unit: str | None = None,
        notes: str | None = None,
    ) -> SemanticMap:
        hypothesis = self.db.query(SemanticHypothesis).filter(SemanticHypothesis.id == hypothesis_id).one()
        device = self.db.query(Device).filter(Device.id == hypothesis.device_id).one_or_none()
        protocol_name = self._infer_protocol_name_from_raw_key(hypothesis.raw_metric_key)

        mapped = self.upsert_operator_map(
            scope=scope,
            device_id=hypothesis.device_id if scope == "device" else None,
            vendor=device.vendor if scope == "vendor" and device is not None else None,
            protocol_name=protocol_name,
            source_key=hypothesis.raw_metric_key,
            metric_key=metric_key or hypothesis.predicted_metric_key,
            unit=unit if unit is not None else hypothesis.predicted_unit,
            notes=notes,
        )

        hypothesis.learning_state = "confirmed"
        hypothesis.predicted_metric_key = mapped.metric_key
        hypothesis.predicted_unit = mapped.unit
        hypothesis.confidence = 1.0
        hypothesis.evidence = f"promoted to semantic map scope={mapped.scope}"
        hypothesis.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(hypothesis)
        return mapped

    @staticmethod
    def _infer_protocol_name_from_raw_key(raw_key: str) -> str:
        prefix = raw_key.split("_", 1)[0].strip().lower()
        protocol_aliases = {
            "mqtt": "mqtt",
            "modbus": "modbus_tcp",
            "snmp": "snmp",
            "opcua": "opc_ua",
            "opc": "opc_ua",
            "dbus": "dbus_gateway",
        }
        return protocol_aliases.get(prefix, prefix or "unknown")
