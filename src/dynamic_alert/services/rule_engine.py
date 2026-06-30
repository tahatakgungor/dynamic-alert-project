from operator import eq, ge, gt, le, lt

from sqlalchemy.orm import Session

from dynamic_alert.models import AlertEvent, AlertRule, TelemetryRecord
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

    def evaluate(self, telemetry: TelemetryRecord) -> list[AlertEvent]:
        rules = (
            self.db.query(AlertRule)
            .filter(AlertRule.enabled.is_(True), AlertRule.metric_key == telemetry.metric_key)
            .all()
        )
        events: list[AlertEvent] = []
        for rule in rules:
            comparator = OPERATORS.get(rule.operator)
            if comparator is None:
                continue
            if comparator(telemetry.value, rule.threshold):
                message = (
                    f"[{rule.severity.upper()}] {telemetry.metric_key}={telemetry.value}{telemetry.unit or ''} "
                    f"esik {rule.operator} {rule.threshold} kosulunu sagladi."
                )
                delivered = self.notifier.send(message)
                event = AlertEvent(
                    rule_id=rule.id,
                    telemetry_id=telemetry.id,
                    message=message,
                    delivered=delivered,
                )
                self.db.add(event)
                events.append(event)
        self.db.commit()
        return events
