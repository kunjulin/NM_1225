from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db.models import Outbox
from app.db.session import get_db
from app.deps.auth import get_login_subject, resolve_acting_role
from app.schemas.admin import OutboxRow
from app.services.errors import error_response
from app.settings import get_settings


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/outbox", response_model=list[OutboxRow])
def list_outbox_route(
    db: Session = Depends(get_db),
    login_subject: str = Depends(get_login_subject),
    x_acting_role: str | None = Header(None, alias="X-Acting-Role"),
):
    settings = get_settings()
    acting_role = resolve_acting_role(x_acting_role, "NM_PHYSICIAN", login_subject)
    if settings.app_mode != "demo" and acting_role != "ADMIN":
        return error_response("FORBIDDEN", "Admin access required.", 403)

    rows = db.query(Outbox).order_by(Outbox.created_at.desc()).all()
    return [
        OutboxRow(
            id=row.id,
            caseId=row.case_id,
            operation=row.operation,
            status=row.status,
            retryCount=row.retry_count,
            lastError=row.last_error,
            createdAt=row.created_at,
            updatedAt=row.updated_at,
            nextRetryAt=row.next_retry_at,
        )
        for row in rows
    ]
