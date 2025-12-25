from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import get_login_subject, resolve_acting_role
from app.schemas.snapshot import (
    AutofillAcceptRequest,
    AutofillAcceptResponse,
    AutofillRejectRequest,
    AutofillRejectResponse,
    SnapshotResponse,
)
from app.services.autofill import accept_autofill, reject_autofill
from app.services.errors import error_response
from app.services.snapshot import get_snapshot


router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("/{caseId}/snapshot", response_model=SnapshotResponse)
def get_snapshot_route(
    caseId: str,
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
) -> SnapshotResponse:
    return get_snapshot(db, caseId, refresh)


@router.post("/{caseId}/autofill/accept", response_model=AutofillAcceptResponse)
def accept_autofill_route(
    caseId: str,
    payload: AutofillAcceptRequest,
    db: Session = Depends(get_db),
    login_subject: str = Depends(get_login_subject),
    x_acting_role: str | None = Header(None, alias="X-Acting-Role"),
):
    if payload.caseId != caseId:
        return error_response("CASE_ID_MISMATCH", "caseId does not match path.", 400)
    acting_role = resolve_acting_role(x_acting_role, "NM_PHYSICIAN", login_subject)
    return accept_autofill(
        db,
        caseId,
        payload.facts,
        payload.reason,
        login_subject,
        acting_role,
    )


@router.post("/{caseId}/autofill/reject", response_model=AutofillRejectResponse)
def reject_autofill_route(
    caseId: str,
    payload: AutofillRejectRequest,
    db: Session = Depends(get_db),
    login_subject: str = Depends(get_login_subject),
    x_acting_role: str | None = Header(None, alias="X-Acting-Role"),
):
    if payload.caseId != caseId:
        return error_response("CASE_ID_MISMATCH", "caseId does not match path.", 400)
    acting_role = resolve_acting_role(x_acting_role, "NM_PHYSICIAN", login_subject)
    return reject_autofill(
        db,
        caseId,
        [item.model_dump() for item in payload.rejections],
        login_subject,
        acting_role,
    )
