from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from dynamic_alert.models import Device, SemanticMap, TelemetryRecord


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
