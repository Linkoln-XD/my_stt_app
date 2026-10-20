from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException


def api_error(
    status_code: int,
    error_type: str,
    message: str,
    *,
    extra: Optional[dict[str, Any]] = None,
) -> HTTPException:
    detail: dict[str, Any] = {"type": error_type, "message": message}
    if extra:
        detail["extra"] = extra
    return HTTPException(status_code=status_code, detail=detail)
