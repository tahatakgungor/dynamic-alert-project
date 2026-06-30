from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dynamic_alert.config import Settings
from dynamic_alert.database import Base
from dynamic_alert.models import Device, FlowCluster, TrafficObservation
from dynamic_alert.services.passive_observation import PacketSample, PassiveObservationService


def test_passive_observation_creates_observations_and_clusters() -> None:
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        db.add(Device(ip_address="192.168.1.20", hostname="plc", vendor="Generic", status="online"))
        db.commit()

        service = PassiveObservationService(db, Settings())
        result = service.ingest_samples(
            [
                PacketSample(
                    source_ip="192.168.1.20",
                    source_port=40001,
                    destination_ip="192.168.1.100",
                    destination_port=502,
                    transport="tcp",
                    payload_sample="010300000002",
                )
            ]
        )

        assert result == {"observations": 1, "new_clusters": 1}
        assert db.query(TrafficObservation).count() == 1
        cluster = db.query(FlowCluster).one()
        assert cluster.protocol_hint == "modbus_tcp"
