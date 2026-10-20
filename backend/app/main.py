import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, transcriptions
from app.services.system_settings import load_system_settings
from app.spa_static import mount_frontend

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="STT App", version="0.2.0")

_cors = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if _cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(admin.router)
app.include_router(transcriptions.router)


@app.on_event("startup")
def _load_runtime_settings() -> None:
    load_system_settings()


@app.get("/api/health")
def health():
    return {"ok": True}


if settings.static_dir:
    mount_frontend(app, settings.static_dir)
