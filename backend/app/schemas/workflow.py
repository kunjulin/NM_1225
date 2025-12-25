from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DraftRequest(BaseModel):
    draft: dict[str, Any]


class SubmitResponse(BaseModel):
    caseId: str
    status: str


class RespondRequest(BaseModel):
    responseAction: str
    comment: str | None = None


class ReturnRequest(BaseModel):
    returnReasonCodes: list[str]
    comment: str | None = None


class ClaimResponse(BaseModel):
    caseId: str
    status: str
    ownerSubject: str


class ApproveResponse(BaseModel):
    caseId: str
    status: str


class CaseStatus(BaseModel):
    caseId: str
    status: str


class BulkFailure(BaseModel):
    caseId: str
    code: str
    message: str


class BulkApproveRequest(BaseModel):
    caseIds: list[str]
    note: str | None = None


class BulkApproveResponse(BaseModel):
    ok: list[CaseStatus]
    failed: list[BulkFailure]
