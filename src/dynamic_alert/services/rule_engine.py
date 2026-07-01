from operator import eq, ge, gt, le, lt

from sqlalchemy.orm import Session

from dynamic_alert.models import AlertEvent, AlertRule, TelemetryRecord
from dynamic_alert.services.audit import AuditLogService
from dynamic_alert.services.telegram import TelegramNotifier

OPERATORS = {
    ">": gt,
    ">=": ge,
    "<": lt,
    "<=": le,
    "==": eq,
}


class RuleEngine:
    def __init__(self, db: Session, notifier: TelegramNotifier) -> None:
        self.db = db
        self.notifier = notifier

    def evaluate(
        self,
        telemetry: TelemetryRecord,
        *,
        semantic_metric_key: str | None = None,
    ) -> list[AlertEvent]:
        metric_keys = {telemetry.metric_key}
        if semantic_metric_key:
            metric_keys.add(semantic_metric_key)

        rules = (
            self.db.query(AlertRule)
            .filter(AlertRule.enabled.is_(True), AlertRule.metric_key.in_(metric_keys))
            .all()
        )
        events: list[AlertEvent] = []
        for rule in rules:
            comparator = OPERATORS.get(rule.operator)
            if comparator is None:
                continue
            if comparator(telemetry.value, rule.threshold):
                semantic_suffix = ""
                if semantic_metric_key and semantic_metric_key != telemetry.metric_key:
                    semantic_suffix = f" semantic_metric={semantic_metric_key} raw_metric={telemetry.metric_key}"
                message = (
                    f"[{rule.severity.upper()}] {rule.metric_key}={telemetry.value}{telemetry.unit or ''} "
                    f"esik {rule.operator} {rule.threshold} kosulunu sagladi.{semantic_suffix}"
                )
                delivered = self.notifier.send(message)
                event = AlertEvent(
                    rule_id=rule.id,
                    telemetry_id=telemetry.id,
                    message=message,
                    delivered=delivered,
                )
                self.db.add(event)
                self.db.flush()
                AuditLogService(self.db).record(
                    actor="system",
                    action="alert.triggered",
                    target=rule.name,
                    status="delivered" if delivered else "pending",
                    details=message,
                )
                events.append(event)
        self.db.commit()
        return events
