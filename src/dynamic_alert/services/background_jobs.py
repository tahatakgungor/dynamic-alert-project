from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
import json
from threading import Lock
from typing import Any, Callable
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from dynamic_alert.database import SessionLocal
from dynamic_alert.models import BackgroundJobRecord


@dataclass(slots=True)
class BackgroundJob:
    id: str
    kind: str
    actor: str
    status: str
    submitted_at: str
    started_at: str | None = None
    finished_at: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BackgroundJobRunner:
    def __init__(self, *, max_workers: int = 2, session_factory: sessionmaker[Session] | None = None) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="dynamic-alert-job")
        self._jobs: dict[str, BackgroundJob] = {}
        self._lock = Lock()
        self._session_factory = session_factory or SessionLocal

    def submit(self, *, kind: str, actor: str, task: Callable[[], dict[str, Any]]) -> BackgroundJob:
        submitted_at = datetime.utcnow().isoformat()
        job = BackgroundJob(
            id=uuid4().hex,
            kind=kind,
            actor=actor,
            status="queued",
            submitted_at=submitted_at,
        )
        with self._lock:
            self._jobs[job.id] = job
        self._persist_job(job)
        self._executor.submit(self._run_job, job.id, task)
        return job

    def get(self, job_id: str) -> BackgroundJob | None:
        with self._lock:
            cached = self._jobs.get(job_id)
        if cached is not None:
            return cached

        db = self._session_factory()
        try:
            record = db.query(BackgroundJobRecord).filter(BackgroundJobRecord.id == job_id).one_or_none()
            return self._from_record(record) if record is not None else None
        finally:
            db.close()

    def list_recent(self, *, limit: int = 50) -> list[BackgroundJob]:
        db = self._session_factory()
        try:
            records = (
                db.query(BackgroundJobRecord)
                .order_by(BackgroundJobRecord.submitted_at.desc())
                .limit(limit)
                .all()
            )
            return [self._from_record(record) for record in records]
        finally:
            db.close()

    def _run_job(self, job_id: str, task: Callable[[], dict[str, Any]]) -> None:
        started_at = datetime.utcnow().isoformat()
        self._update(job_id, status="running", started_at=started_at, error=None)
        try:
            result = task()
        except Exception as exc:
            self._update(
                job_id,
                status="failed",
                finished_at=datetime.utcnow().isoformat(),
                error=str(exc),
            )
            return

        self._update(
            job_id,
            status="completed",
            finished_at=datetime.utcnow().isoformat(),
            result=result,
        )

    def _update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)
        self._persist_job(job)

    def _persist_job(self, job: BackgroundJob) -> None:
        db = self._session_factory()
        try:
            record = db.query(BackgroundJobRecord).filter(BackgroundJobRecord.id == job.id).one_or_none()
            if record is None:
                record = BackgroundJobRecord(
                    id=job.id,
                    kind=job.kind,
                    actor=job.actor,
                    status=job.status,
                    submitted_at=_parse_dt(job.submitted_at) or datetime.utcnow(),
                )
                db.add(record)

            record.kind = job.kind
            record.actor = job.actor
            record.status = job.status
            record.submitted_at = _parse_dt(job.submitted_at) or record.submitted_at
            record.started_at = _parse_dt(job.started_at)
            record.finished_at = _parse_dt(job.finished_at)
            record.result_json = json.dumps(job.result) if job.result is not None else None
            record.error = job.error
            db.commit()
        finally:
            db.close()

    @staticmethod
    def _from_record(record: BackgroundJobRecord) -> BackgroundJob:
        result = None
        if record.result_json:
            try:
                parsed = json.loads(record.result_json)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                result = parsed

        return BackgroundJob(
            id=record.id,
            kind=record.kind,
            actor=record.actor,
            status=record.status,
            submitted_at=record.submitted_at.isoformat(),
            started_at=record.started_at.isoformat() if record.started_at else None,
            finished_at=record.finished_at.isoformat() if record.finished_at else None,
            result=result,
            error=record.error,
        )


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


_runner: BackgroundJobRunner | None = None


def get_background_job_runner() -> BackgroundJobRunner:
    global _runner
    if _runner is None:
        _runner = BackgroundJobRunner()
    return _runner
