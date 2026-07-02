from __future__ import annotations

import re

from sqlalchemy.orm import Session

from dynamic_alert.models import AuditLog


MAX_AUDIT_DETAIL_LENGTH = 512
TOKEN_PATTERNS = [
    re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)(token|api[_-]?key|node[_-]?key|secret|password)(\s*[:=]\s*)([^,\s]+)"),
]


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
                details=self._sanitize_details(details),
            )
        )
        self.db.commit()

    @staticmethod
    def _sanitize_details(details: str | None) -> str | None:
        if details is None:
            return None
        cleaned = details
        cleaned = TOKEN_PATTERNS[0].sub("[redacted-token]", cleaned)
        cleaned = TOKEN_PATTERNS[1].sub(r"\1\2[redacted]", cleaned)
        if len(cleaned) > MAX_AUDIT_DETAIL_LENGTH:
            cleaned = f"{cleaned[:MAX_AUDIT_DETAIL_LENGTH]}...[truncated]"
        return cleaned
