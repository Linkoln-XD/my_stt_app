from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.auth.admin_session import create_session, validate_session, verify_admin_credentials
from app.services.api_errors import api_error
from app.services.system_settings import (
    ALLOWED_DURATION_MINUTES,
    ModelTier,
    SystemSettings,
    load_system_settings,
    save_system_settings,
)

router = APIRouter(prefix="/api", tags=["admin"])


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    token: str


class PublicSettingsResponse(BaseModel):
    model_tier: ModelTier
    max_duration_minutes: int
    allowed_duration_minutes: list[int]
    model_tiers: list[Literal["light", "medium", "heavy"]]


class AdminSettingsUpdate(BaseModel):
    model_tier: Optional[ModelTier] = None
    max_duration_minutes: Optional[int] = Field(default=None, ge=1, le=120)


def require_admin(x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token")) -> str:
    if not validate_session(x_admin_token):
        raise api_error(401, "admin_unauthorized", "Требуется вход администратора")
    return x_admin_token  # type: ignore[return-value]


@router.get("/settings/public", response_model=PublicSettingsResponse)
def get_public_settings():
    s = load_system_settings()
    return PublicSettingsResponse(
        model_tier=s.model_tier,
        max_duration_minutes=s.max_duration_minutes,
        allowed_duration_minutes=list(ALLOWED_DURATION_MINUTES),
        model_tiers=["light", "medium", "heavy"],
    )


@router.post("/admin/login", response_model=AdminLoginResponse)
def admin_login(body: AdminLoginRequest):
    if not verify_admin_credentials(body.username, body.password):
        raise api_error(401, "admin_invalid_credentials", "Неверный логин или пароль администратора")
    return AdminLoginResponse(token=create_session())


@router.get("/admin/settings", response_model=SystemSettings)
def get_admin_settings(_token: str = Depends(require_admin)):
    return load_system_settings()


@router.patch("/admin/settings", response_model=SystemSettings)
def patch_admin_settings(body: AdminSettingsUpdate, _token: str = Depends(require_admin)):
    current = load_system_settings()
    updated = current.model_copy(
        update={k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    )
    try:
        return save_system_settings(updated)
    except ValueError as exc:
        raise api_error(400, "invalid_settings", str(exc)) from exc
