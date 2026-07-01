from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from typing import Any
from urllib import error, request

from dynamic_alert.config import Settings
from dynamic_alert.database import Base, SessionLocal, engine
from dynamic_alert.services.audit import AuditLogService
from dynamic_alert.services.container import create_ingestion_coordinator
from dynamic_alert.services.discovery import NetworkDiscoveryService
from dynamic_alert.services.job_execution import (
    apply_settings_overrides,
    execute_dbus_demo,
    execute_live_capture,
    execute_passive_observe,
    execute_scan,
)
from dynamic_alert.services.passive_observation import PassiveObservationService


class EdgeControlPlaneClient:
    def __init__(self, *, base_url: str, edge_key: str | None = None, admin_api_key: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.edge_key = edge_key
        self.admin_api_key = admin_api_key

    def register_node(
        self,
        *,
        name: str,
        site_code: str | None,
        hostname: str | None,
        software_version: str | None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/edge/register",
            payload={
                "name": name,
                "site_code": site_code,
                "hostname": hostname,
                "software_version": software_version,
            },
            api_key=self.admin_api_key,
        )

    def heartbeat(self, *, software_version: str | None, status: str = "online") -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/edge/heartbeat",
            payload={"software_version": software_version, "status": status},
            edge_key=self.edge_key,
        )

    def claim_next_job(self) -> dict[str, Any]:
        return self._request("POST", "/api/edge/claim-next-job", edge_key=self.edge_key)

    def complete_job(self, *, job_id: int, status: str, result: dict[str, Any] | None, error_text: str | None) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/edge-jobs/{job_id}/complete",
            payload={"status": status, "result": result, "error": error_text},
            edge_key=self.edge_key,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        api_key: str | None = None,
        edge_key: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key
        if edge_key:
            headers["X-Edge-Key"] = edge_key
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = request.Request(f"{self.base_url}{path}", data=body, headers=headers, method=method)
        with request.urlopen(req, timeout=10.0) as response:
            raw = response.read().decode("utf-8", errors="ignore")
        return json.loads(raw) if raw else {}


class EdgeAgentRunner:
    def __init__(self, *, settings: Settings, client: EdgeControlPlaneClient) -> None:
        self.settings = settings
        self.client = client

    def run_once(self) -> dict[str, Any]:
        Base.metadata.create_all(bind=engine)
        self.client.heartbeat(software_version=self.settings.app_name, status="online")
        claimed = self.client.claim_next_job()
        if claimed.get("status") == "empty":
            return {"status": "empty"}

        job_id = int(claimed["id"])
        job_kind = str(claimed["job_kind"])
        try:
            result = self._execute_job(job_kind, claimed.get("payload"))
        except Exception as exc:
            self.client.complete_job(job_id=job_id, status="failed", result=None, error_text=str(exc))
            raise

        self.client.complete_job(job_id=job_id, status="completed", result=result, error_text=None)
        return {"status": "completed", "job_id": job_id, "job_kind": job_kind, "result": result}

    def run_forever(self) -> None:
        while True:
            try:
                self.run_once()
            except error.URLError as exc:
                print(f"[edge-agent] control plane unreachable: {exc}", file=sys.stderr)
                time.sleep(max(self.settings.edge_poll_interval_seconds, 1.0))
                continue
            except Exception as exc:
                print(f"[edge-agent] job loop error: {exc}", file=sys.stderr)
                time.sleep(max(self.settings.edge_poll_interval_seconds, 1.0))
                continue
            time.sleep(max(self.settings.edge_poll_interval_seconds, 1.0))

    def _execute_job(self, job_kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        db = SessionLocal()
        try:
            payload = payload or {}
            effective_settings = apply_settings_overrides(self.settings, payload)
            enabled_protocol_names = payload.get("enabled_protocols")
            if job_kind == "scan":
                discovery = NetworkDiscoveryService(effective_settings.scan_subnets)
                result = execute_scan(
                    create_ingestion_coordinator(
                        db,
                        settings=effective_settings,
                        discovery=discovery,
                        enabled_protocol_names=enabled_protocol_names if isinstance(enabled_protocol_names, list) else None,
                    )
                )
            elif job_kind == "passive-observe":
                result = execute_passive_observe(PassiveObservationService(db, effective_settings), payload)
            elif job_kind == "live-capture":
                result = execute_live_capture(PassiveObservationService(db, effective_settings))
            elif job_kind == "dbus-demo":
                result = execute_dbus_demo(
                    create_ingestion_coordinator(
                        db,
                        settings=effective_settings,
                        enabled_protocol_names=enabled_protocol_names if isinstance(enabled_protocol_names, list) else None,
                    ),
                    payload,
                )
            else:
                raise ValueError(f"unsupported edge job kind: {job_kind}")
            AuditLogService(db).record(actor=self.settings.edge_node_name, action=f"edge-agent.{job_kind}", target="local", details=str(result))
            return result
        finally:
            db.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="dynamic-alert-edge-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_parser = subparsers.add_parser("register")
    register_parser.add_argument("--control-plane-url", required=False)
    register_parser.add_argument("--admin-api-key", required=True)
    register_parser.add_argument("--name", required=False)
    register_parser.add_argument("--site-code", required=False)
    register_parser.add_argument("--software-version", required=False, default="0.1.0")

    run_once_parser = subparsers.add_parser("run-once")
    run_once_parser.add_argument("--control-plane-url", required=False)
    run_once_parser.add_argument("--edge-key", required=False)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--control-plane-url", required=False)
    run_parser.add_argument("--edge-key", required=False)

    args = parser.parse_args()
    settings = Settings()

    if args.command == "register":
        client = EdgeControlPlaneClient(
            base_url=args.control_plane_url or settings.control_plane_url,
            admin_api_key=args.admin_api_key,
        )
        payload = client.register_node(
            name=args.name or settings.edge_node_name,
            site_code=args.site_code or settings.edge_site_code,
            hostname=socket.gethostname(),
            software_version=args.software_version,
        )
        print(json.dumps(payload))
        return

    edge_key = args.edge_key or settings.edge_node_key
    if not edge_key:
        raise SystemExit("edge key is required")
    client = EdgeControlPlaneClient(
        base_url=args.control_plane_url or settings.control_plane_url,
        edge_key=edge_key,
    )
    runner = EdgeAgentRunner(settings=settings, client=client)
    if args.command == "run-once":
        print(json.dumps(runner.run_once()))
        return
    runner.run_forever()


if __name__ == "__main__":
    main()
