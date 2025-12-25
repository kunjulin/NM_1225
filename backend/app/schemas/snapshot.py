from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CandidateFact(BaseModel):
    factType: str
    value: str | float | int
    unit: str
    asOf: str
    sourceType: str
    sourceRef: str
    sourceSnippet: str | None = None
    confidence: str
    extractionMethod: str


class SnapshotResponse(BaseModel):
    caseId: str
    patientRef: str
    serviceRequestRef: str
    snapshot: dict[str, Any]
    candidateFacts: list[CandidateFact]


class AutofillAcceptRequest(BaseModel):
    caseId: str
    facts: list[CandidateFact]
    reason: str | None = None


class AutofillAcceptResponse(BaseModel):
    caseId: str
    updatedLocalFacts: dict[str, Any]
    cds: dict[str, Any]


class AutofillRejectItem(BaseModel):
    factType: str
    sourceRef: str
    reason: str | None = None


class AutofillRejectRequest(BaseModel):
    caseId: str
    rejections: list[AutofillRejectItem]


class AutofillRejectResponse(BaseModel):
    caseId: str
    rejected: bool
