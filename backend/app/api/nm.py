from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import get_login_subject, resolve_acting_role
from app.schemas.workflow import DraftRequest, RespondRequest, SubmitResponse
from app.schemas.worklist import WorklistItem, WorklistResponse
from app.services.workflow import respond_case, submit_case, update_draft
from app.services.worklist import get_nm_worklist


router = APIRouter(prefix="/nm", tags=["nm"])


@router.get("/worklist", response_model=WorklistResponse)
def get_nm_worklist_route(
    status: str | None = Query(None, pattern="^(NM_PENDING|RETURNED|NM_DRAFTED)$"),
    db: Session = Depends(get_db),
) -> WorklistResponse:
    statuses = [status] if status else None
    return get_nm_worklist(db, statuses)


@router.post("/cases/{caseId}/draft", response_model=WorklistItem)
def update_draft_route(
    caseId: str,
    payload: DraftRequest,
    db: Session = Depends(get_db),
    login_subject: str = Depends(get_login_subject),
    x_acting_role: str | None = Header(None, alias="X-Acting-Role"),
):
    acting_role = resolve_acting_role(x_acting_role, "NM_PHYSICIAN", login_subject)
    return update_draft(db, caseId, payload.draft, login_subject, acting_role)


@router.post("/cases/{caseId}/submit", response_model=SubmitResponse)
def submit_case_route(
    caseId: str,
    db: Session = Depends(get_db),
    login_subject: str = Depends(get_login_subject),
    x_acting_role: str | None = Header(None, alias="X-Acting-Role"),
):
    acting_role = resolve_acting_role(x_acting_role, "NM_PHYSICIAN", login_subject)
    return submit_case(db, caseId, login_subject, acting_role)


@router.post("/cases/{caseId}/respond", response_model=SubmitResponse)
def respond_case_route(
    caseId: str,
    payload: RespondRequest,
    db: Session = Depends(get_db),
    login_subject: str = Depends(get_login_subject),
    x_acting_role: str | None = Header(None, alias="X-Acting-Role"),
):
    acting_role = resolve_acting_role(x_acting_role, "NM_PHYSICIAN", login_subject)
    return respond_case(
        db,
        caseId,
        payload.responseAction,
        payload.comment,
        login_subject,
        acting_role,
    )
