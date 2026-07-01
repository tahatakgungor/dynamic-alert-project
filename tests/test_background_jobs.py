import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert.database import Base
from dynamic_alert.models import BackgroundJobRecord
from dynamic_alert.services.background_jobs import BackgroundJobRunner


def test_background_job_runner_completes_task_and_persists_record(tmp_path) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    runner = BackgroundJobRunner(max_workers=1, session_factory=SessionLocal)
    job = runner.submit(kind="unit-test", actor="tester", task=lambda: {"ok": 1})

    for _ in range(20):
        current = runner.get(job.id)
        assert current is not None
        if current.status == "completed":
            assert current.result == {"ok": 1}
            assert current.error is None
            break
        time.sleep(0.05)
    else:
        raise AssertionError("job did not complete in time")

    with SessionLocal() as db:
        record = db.query(BackgroundJobRecord).filter(BackgroundJobRecord.id == job.id).one()
        assert record.status == "completed"
        assert record.result_json == '{"ok": 1}'


def test_background_job_runner_marks_failures_in_db(tmp_path) -> None:
    db_path = tmp_path / "jobs-fail.sqlite3"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    runner = BackgroundJobRunner(max_workers=1, session_factory=SessionLocal)
    job = runner.submit(kind="failing-test", actor="tester", task=lambda: _raise_runtime_error())

    for _ in range(20):
        current = runner.get(job.id)
        assert current is not None
        if current.status == "failed":
            assert "boom" in (current.error or "")
            break
        time.sleep(0.05)
    else:
        raise AssertionError("job did not fail in time")

    with SessionLocal() as db:
        record = db.query(BackgroundJobRecord).filter(BackgroundJobRecord.id == job.id).one()
        assert record.status == "failed"
        assert "boom" in (record.error or "")


def _raise_runtime_error() -> dict[str, int]:
    raise RuntimeError("boom")
