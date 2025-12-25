from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import get_login_subject
from app.deps.demo_mode import require_demo_mode
from app.services.demo_seed import seed_demo_cases
from app.services.demo_state import get_acting_role, set_acting_role
from app.settings import get_settings


router = APIRouter(prefix="/demo", tags=["demo"], dependencies=[Depends(require_demo_mode)])


class SetActingRoleRequest(BaseModel):
    actingRole: str


class WhoAmIResponse(BaseModel):
    subject: str
    actingRole: str
    appMode: str


@router.post("/seed")
def seed_demo_route(
    db: Session = Depends(get_db),
    login_subject: str = Depends(get_login_subject),
):
    acting_role = get_acting_role(login_subject) or "ADMIN"
    return seed_demo_cases(db, login_subject, acting_role)


@router.post("/set-acting-role")
def set_acting_role_route(
    payload: SetActingRoleRequest,
    login_subject: str = Depends(get_login_subject),
):
    set_acting_role(login_subject, payload.actingRole)
    return {"subject": login_subject, "actingRole": payload.actingRole}


@router.get("/whoami", response_model=WhoAmIResponse)
def whoami_route(
    login_subject: str = Depends(get_login_subject),
):
    settings = get_settings()
    return {
        "subject": login_subject,
        "actingRole": payload_acting_role(login_subject),
        "appMode": settings.app_mode,
    }


def payload_acting_role(subject: str) -> str:
    settings = get_settings()
    if settings.app_mode != "demo":
        return "NM_PHYSICIAN"
    return get_acting_role(subject) or "NM_PHYSICIAN"
