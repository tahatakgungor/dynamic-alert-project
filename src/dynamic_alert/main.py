from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dynamic_alert.api.routes import router
from dynamic_alert.config import get_settings
from dynamic_alert.database import Base, SessionLocal, engine
from dynamic_alert.models import AlertRule

settings = get_settings()


def bootstrap_defaults() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
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
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap_defaults()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
