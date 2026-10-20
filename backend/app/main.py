import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin, transcriptions
from app.services.system_settings import load_system_settings

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="STT App", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
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
