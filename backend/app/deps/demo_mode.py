from __future__ import annotations

from fastapi import HTTPException

from app.settings import get_settings


def require_demo_mode() -> None:
    settings = get_settings()
    if settings.app_mode != "demo":
        raise HTTPException(status_code=404, detail="Not found")
