from sqlalchemy.orm import Session

from dynamic_alert.config import Settings
from dynamic_alert.models import AlertRule, ApiClient, IntegrationEndpoint, NetworkSegment, Site, Workspace


def bootstrap_defaults(db: Session, settings: Settings) -> None:
    workspace = db.query(Workspace).filter(Workspace.slug == "default-workspace").one_or_none()
    if workspace is None:
        workspace = Workspace(name="Default Workspace", slug="default-workspace")
        db.add(workspace)
        db.commit()
        db.refresh(workspace)

    site = db.query(Site).filter(Site.code == "HQ-PLANT").one_or_none()
    if site is None:
        site = Site(
            workspace_id=workspace.id,
            name="HQ Plant",
            code="HQ-PLANT",
            timezone="Europe/Istanbul",
        )
        db.add(site)
        db.commit()
        db.refresh(site)

    for cidr in settings.scan_subnets:
        segment = db.query(NetworkSegment).filter(NetworkSegment.cidr == cidr).one_or_none()
        if segment is None:
            db.add(NetworkSegment(site_id=site.id, cidr=cidr, label=f"Primary Segment {cidr}"))
    db.commit()

    if db.query(IntegrationEndpoint).filter(IntegrationEndpoint.name == "Telegram Alerts").one_or_none() is None:
        db.add(
            IntegrationEndpoint(
                site_id=site.id,
                name="Telegram Alerts",
                kind="telegram",
                status="dry-run" if not settings.telegram_bot_token else "configured",
                target_ref=settings.telegram_chat_id,
            )
        )
        db.commit()

    if db.query(ApiClient).filter(ApiClient.name == "bootstrap-admin").one_or_none() is None:
        db.add(
            ApiClient(
                name="bootstrap-admin",
                client_key=settings.bootstrap_api_key,
                role="admin",
            )
        )
        db.commit()

    existing = db.query(AlertRule).filter(AlertRule.name == "High Temperature").one_or_none()
    if existing is None:
        db.add(
            AlertRule(
                name="High Temperature",
                metric_key="temperature_c",
                operator=">",
                threshold=70.0,
                severity="critical",
            )
        )
        db.commit()
