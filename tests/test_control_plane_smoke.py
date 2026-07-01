from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert import database as database_module
from dynamic_alert.models import AlertEvent, TelemetryRecord
from dynamic_alert.main import app
import dynamic_alert.main as main_module


class SmokeEdgeClient:
    def __init__(self, client: TestClient, *, edge_key: str) -> None:
        self.client = client
        self.edge_key = edge_key

    def heartbeat(self, *, software_version: str | None, status: str = "online") -> dict:
        response = self.client.post(
            "/api/edge/heartbeat",
            headers={"X-Edge-Key": self.edge_key},
            json={"software_version": software_version, "status": status},
        )
        assert response.status_code == 200
        return response.json()

    def claim_next_job(self) -> dict:
        response = self.client.post("/api/edge/claim-next-job", headers={"X-Edge-Key": self.edge_key})
        assert response.status_code == 200
        return response.json()

    def complete_job(self, *, job_id: int, status: str, result: dict | None, error_text: str | None) -> dict:
        response = self.client.post(
            f"/api/edge-jobs/{job_id}/complete",
            headers={"X-Edge-Key": self.edge_key},
            json={"status": status, "result": result, "error": error_text},
        )
        assert response.status_code == 200
        return response.json()


def test_control_plane_edge_roundtrip_executes_dbus_demo(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "smoke.sqlite3"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(database_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(main_module, "engine", engine)
    monkeypatch.setattr(main_module, "SessionLocal", test_session_local)

    import dynamic_alert.edge_agent as edge_agent_module
    from dynamic_alert.edge_agent import EdgeAgentRunner
    from dynamic_alert.config import Settings

    monkeypatch.setattr(edge_agent_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(edge_agent_module, "engine", engine)

    with TestClient(app) as client:
        register = client.post(
            "/api/edge/register",
            headers={"X-API-Key": "change-me-before-production"},
            json={
                "name": "factory-edge-01",
                "site_code": "HQ-PLANT",
                "hostname": "factory-edge-host",
                "software_version": "0.1.0",
            },
        )
        assert register.status_code == 200
        edge_payload = register.json()
        edge_key = edge_payload["node_key"]
        edge_node_id = edge_payload["id"]

        enqueue = client.post(
            "/api/edge-jobs",
            headers={"X-API-Key": "change-me-before-production"},
            json={
                "edge_node_id": edge_node_id,
                "job_kind": "dbus-demo",
                "payload": {
                    "site_code": "HQ-PLANT",
                    "ip_address": "192.168.10.50",
                    "hostname": "edge-temp-gw",
                    "vendor": "Linux Edge Gateway",
                    "open_ports": [22, 80],
                },
            },
        )
        assert enqueue.status_code == 200

        runner = EdgeAgentRunner(
            settings=Settings(edge_node_name="factory-edge-01"),
            client=SmokeEdgeClient(client, edge_key=edge_key),  # type: ignore[arg-type]
        )
        result = runner.run_once()

        assert result["status"] == "completed"
        assert result["job_kind"] == "dbus-demo"
        assert result["result"]["telemetry_records"] == 1

        edge_jobs = client.get("/api/edge-jobs", headers={"X-API-Key": "change-me-before-production"})
        assert edge_jobs.status_code == 200
        jobs_payload = edge_jobs.json()
        assert jobs_payload[0]["status"] == "completed"

        with test_session_local() as db:
            telemetry = db.query(TelemetryRecord).order_by(TelemetryRecord.id.desc()).first()
            assert telemetry is not None
            assert telemetry.metric_key == "dbus_sensor_temperature_raw"
            alert = db.query(AlertEvent).order_by(AlertEvent.id.desc()).first()
            assert alert is not None
            assert "temperature_c" in alert.message

        alerts = client.get("/api/alert-events", headers={"X-API-Key": "change-me-before-production"})
        assert alerts.status_code == 200
        alert_payload = alerts.json()
        assert any("temperature_c" in item["message"] for item in alert_payload)
