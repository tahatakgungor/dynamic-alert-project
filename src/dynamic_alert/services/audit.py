from __future__ import annotations

from sqlalchemy.orm import Session

from dynamic_alert.models import AuditLog


class AuditLogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(self, *, actor: str, action: str, target: str, status: str = "ok", details: str | None = None) -> None:
        self.db.add(
            AuditLog(
                actor=actor,
                action=action,
                target=target,
                status=status,
                details=details,
            )
        )
        self.db.commit()
