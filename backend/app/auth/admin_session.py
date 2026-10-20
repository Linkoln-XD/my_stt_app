from __future__ import annotations

import secrets
import threading
import time
from typing import Optional

from app.config import settings

SESSION_TTL_SEC = 8 * 3600
_sessions: dict[str, float] = {}
_lock = threading.Lock()


def verify_admin_credentials(username: str, password: str) -> bool:
    return (
        username == settings.admin_username
        and password == settings.admin_password
    )


def create_session() -> str:
    token = secrets.token_urlsafe(32)
    with _lock:
        _sessions[token] = time.time() + SESSION_TTL_SEC
    return token


def validate_session(token: Optional[str]) -> bool:
    if not token:
        return False
    now = time.time()
    with _lock:
        expires = _sessions.get(token)
        if not expires:
            return False
        if expires < now:
            del _sessions[token]
            return False
        return True
