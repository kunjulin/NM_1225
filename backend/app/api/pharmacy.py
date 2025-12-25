from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import get_login_subject, resolve_acting_role
from app.schemas.workflow import (
    ApproveResponse,
    BulkApproveRequest,
    BulkApproveResponse,
    ClaimResponse,
    ReturnRequest,
    SubmitResponse,
)
from app.schemas.worklist import WorklistResponse
from app.services.workflow import (
    approve_case,
    bulk_approve,
    claim_case,
    return_case,
)
from app.services.worklist import get_pharmacy_worklist


router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])


@router.get("/worklist", response_model=WorklistResponse)
def get_pharmacy_worklist_route(
    status: str | None = Query(None, pattern="^(PHARM_READY|PHARM_IN_PROGRESS)$"),
    db: Session = Depends(get_db),
    login_subject: str = Depends(get_login_subject),
) -> WorklistResponse:
    statuses = [status] if status else None
    return get_pharmacy_worklist(db, statuses, login_subject)


@router.post("/cases/{caseId}/claim", response_model=ClaimResponse)
def claim_case_route(
    caseId: str,
    db: Session = Depends(get_db),
    login_subject: str = Depends(get_login_subject),
    x_acting_role: str | None = Header(None, alias="X-Acting-Role"),
):
    acting_role = resolve_acting_role(x_acting_role, "PHARMACIST", login_subject)
    return claim_case(db, caseId, login_subject, acting_role)


@router.post("/cases/{caseId}/approve", response_model=ApproveResponse)
def approve_case_route(
    caseId: str,
    db: Session = Depends(get_db),
    login_subject: str = Depends(get_login_subject),
    x_acting_role: str | None = Header(None, alias="X-Acting-Role"),
):
    acting_role = resolve_acting_role(x_acting_role, "PHARMACIST", login_subject)
    return approve_case(db, caseId, login_subject, acting_role)


@router.post("/cases/{caseId}/return", response_model=SubmitResponse)
def return_case_route(
    caseId: str,
    payload: ReturnRequest,
    db: Session = Depends(get_db),
    login_subject: str = Depends(get_login_subject),
    x_acting_role: str | None = Header(None, alias="X-Acting-Role"),
):
    acting_role = resolve_acting_role(x_acting_role, "PHARMACIST", login_subject)
    return return_case(
        db,
        caseId,
        payload.returnReasonCodes,
        payload.comment,
        login_subject,
        acting_role,
    )


@router.post("/bulk-approve", response_model=BulkApproveResponse)
def bulk_approve_route(
    payload: BulkApproveRequest,
    db: Session = Depends(get_db),
    login_subject: str = Depends(get_login_subject),
    x_acting_role: str | None = Header(None, alias="X-Acting-Role"),
):
    acting_role = resolve_acting_role(x_acting_role, "PHARMACIST", login_subject)
    return bulk_approve(
        db,
        payload.caseIds,
        payload.note,
        login_subject,
        acting_role,
    )
