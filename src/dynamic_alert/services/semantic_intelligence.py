from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from dynamic_alert.config import Settings
from dynamic_alert.models import SemanticHypothesis, TelemetryRecord
from dynamic_alert.services.semantic_map import SemanticMapService


@dataclass(slots=True)
class SemanticPrediction:
    metric_key: str
    unit: str | None
    confidence: float
    evidence: str
    learning_state: str


class SemanticIntelligenceService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.semantic_map_service = SemanticMapService(db)

    def learn_from_telemetry(self, telemetry: TelemetryRecord) -> SemanticHypothesis | None:
        if not self.settings.local_ai_enabled:
            return None

        resolved_map = self.semantic_map_service.resolve_for_telemetry(telemetry)
        if resolved_map is not None:
            prediction = SemanticPrediction(
                metric_key=resolved_map.metric_key,
                unit=resolved_map.unit,
                confidence=resolved_map.confidence,
                evidence=f"resolved from semantic map scope={resolved_map.scope}",
                learning_state="confirmed",
            )
        else:
            prediction = self._predict_semantics(telemetry)
        hypothesis = (
            self.db.query(SemanticHypothesis)
            .filter(
                SemanticHypothesis.device_id == telemetry.device_id,
                SemanticHypothesis.raw_metric_key == telemetry.metric_key,
            )
            .one_or_none()
        )

        if hypothesis is None:
            hypothesis = SemanticHypothesis(
                device_id=telemetry.device_id,
                raw_metric_key=telemetry.metric_key,
                predicted_metric_key=prediction.metric_key,
                predicted_unit=prediction.unit,
                confidence=prediction.confidence,
                evidence=prediction.evidence,
                learning_state=prediction.learning_state,
                last_observed_value=telemetry.value,
                observation_count=1,
                updated_at=datetime.utcnow(),
            )
            self.db.add(hypothesis)
        else:
            hypothesis.predicted_metric_key = prediction.metric_key
            hypothesis.predicted_unit = prediction.unit
            hypothesis.confidence = min(0.99, (hypothesis.confidence + prediction.confidence) / 2)
            hypothesis.evidence = prediction.evidence
            hypothesis.learning_state = prediction.learning_state
            hypothesis.last_observed_value = telemetry.value
            hypothesis.observation_count += 1
            hypothesis.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(hypothesis)
        return hypothesis

    def _predict_semantics(self, telemetry: TelemetryRecord) -> SemanticPrediction:
        key = telemetry.metric_key.lower()
        source = telemetry.source_protocol.lower()
        value = telemetry.value

        if "press" in key or "bar" in key or (0 <= value <= 20 and "modbus" in source):
            return SemanticPrediction(
                metric_key="pressure_bar",
                unit="bar",
                confidence=0.72,
                evidence=f"key={telemetry.metric_key}, source={telemetry.source_protocol}, value_range=0-20",
                learning_state="learning",
            )
        if "temp" in key or key.endswith("_c") or (0 <= value <= 200 and "modbus" in source):
            return SemanticPrediction(
                metric_key="temperature_c",
                unit="C",
                confidence=0.78,
                evidence=f"key={telemetry.metric_key}, source={telemetry.source_protocol}, value_range=0-200",
                learning_state="learning",
            )
        if "vib" in key or "accel" in key:
            return SemanticPrediction(
                metric_key="vibration_index",
                unit="g",
                confidence=0.68,
                evidence=f"key={telemetry.metric_key} matches vibration heuristic",
                learning_state="candidate",
            )
        return SemanticPrediction(
            metric_key=telemetry.metric_key,
            unit=telemetry.unit,
            confidence=0.35,
            evidence=f"fallback semantic retention for {telemetry.metric_key}",
            learning_state="candidate",
        )
