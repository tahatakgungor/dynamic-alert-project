from dynamic_alert.config import Settings
from dynamic_alert.edge_agent import EdgeAgentRunner


class FakeClient:
    def __init__(self, claimed_job: dict) -> None:
        self.claimed_job = claimed_job
        self.completed: list[dict] = []
        self.heartbeats: list[dict] = []

    def heartbeat(self, *, software_version: str | None, status: str = "online") -> dict:
        payload = {"software_version": software_version, "status": status}
        self.heartbeats.append(payload)
        return payload

    def claim_next_job(self) -> dict:
        return self.claimed_job

    def complete_job(self, *, job_id: int, status: str, result: dict | None, error_text: str | None) -> dict:
        payload = {
            "job_id": job_id,
            "status": status,
            "result": result,
            "error_text": error_text,
        }
        self.completed.append(payload)
        return payload


def test_edge_agent_runner_completes_claimed_job(monkeypatch) -> None:
    client = FakeClient({"id": 12, "job_kind": "scan", "status": "running", "payload": None})
    runner = EdgeAgentRunner(settings=Settings(edge_node_name="factory-edge-01"), client=client)  # type: ignore[arg-type]

    monkeypatch.setattr("dynamic_alert.edge_agent.Base.metadata.create_all", lambda bind: None)
    monkeypatch.setattr(runner, "_execute_job", lambda job_kind, payload=None: {"new_devices": 2, "telemetry_records": 4})

    result = runner.run_once()

    assert result["status"] == "completed"
    assert result["job_id"] == 12
    assert client.heartbeats
    assert client.completed == [
        {
            "job_id": 12,
            "status": "completed",
            "result": {"new_devices": 2, "telemetry_records": 4},
            "error_text": None,
        }
    ]


def test_edge_agent_runner_returns_empty_when_no_job(monkeypatch) -> None:
    client = FakeClient({"status": "empty"})
    runner = EdgeAgentRunner(settings=Settings(edge_node_name="factory-edge-01"), client=client)  # type: ignore[arg-type]

    monkeypatch.setattr("dynamic_alert.edge_agent.Base.metadata.create_all", lambda bind: None)

    result = runner.run_once()

    assert result == {"status": "empty"}
    assert client.completed == []


def test_edge_agent_runner_passes_payload_to_execution(monkeypatch) -> None:
    client = FakeClient(
        {
            "id": 21,
            "job_kind": "scan",
            "status": "running",
            "payload": {"scan_subnets": ["10.20.30.0/24"]},
        }
    )
    runner = EdgeAgentRunner(settings=Settings(edge_node_name="factory-edge-01"), client=client)  # type: ignore[arg-type]
    captured: dict[str, object] = {}

    monkeypatch.setattr("dynamic_alert.edge_agent.Base.metadata.create_all", lambda bind: None)

    def fake_execute(job_kind, payload=None):
        captured["job_kind"] = job_kind
        captured["payload"] = payload
        return {"ok": 1}

    monkeypatch.setattr(runner, "_execute_job", fake_execute)

    result = runner.run_once()

    assert result["status"] == "completed"
    assert captured["job_kind"] == "scan"
    assert captured["payload"] == {"scan_subnets": ["10.20.30.0/24"]}
