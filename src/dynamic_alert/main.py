from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dynamic_alert.api.routes import router
from dynamic_alert.bootstrap import bootstrap_defaults
from dynamic_alert.config import get_settings
from dynamic_alert.database import Base, SessionLocal, engine

settings = get_settings()


def initialize_platform() -> None:
    settings.validate_security()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        bootstrap_defaults(db, settings)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_platform()
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
