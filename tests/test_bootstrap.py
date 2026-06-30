from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert.bootstrap import bootstrap_defaults
from dynamic_alert.config import Settings
from dynamic_alert.database import Base
from dynamic_alert.models import ApiClient, IntegrationEndpoint, NetworkSegment, Site, Workspace


def test_bootstrap_creates_platform_defaults() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    settings = Settings(scan_subnets_raw="192.168.1.0/24,10.10.0.0/24")

    with SessionLocal() as db:
        bootstrap_defaults(db, settings)

        assert db.query(Workspace).count() == 1
        assert db.query(Site).count() == 1
        assert db.query(NetworkSegment).count() == 2
        assert db.query(IntegrationEndpoint).count() == 1
        assert db.query(ApiClient).count() == 1
