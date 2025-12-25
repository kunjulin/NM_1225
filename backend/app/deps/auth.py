from __future__ import annotations

from fastapi import Header

from app.services.demo_state import get_acting_role as get_demo_acting_role
from app.settings import get_settings


def get_login_subject(x_subject: str | None = Header(None, alias="X-Subject")) -> str:
    return x_subject or "demo-user"


def resolve_acting_role(
    x_acting_role: str | None,
    default_role: str,
    login_subject: str,
) -> str:
    if x_acting_role:
        return x_acting_role
    settings = get_settings()
    if settings.app_mode == "demo":
        stored = get_demo_acting_role(login_subject)
        if stored:
            return stored
    return default_role
