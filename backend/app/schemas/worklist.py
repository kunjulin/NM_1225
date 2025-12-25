from __future__ import annotations

from pydantic import BaseModel


class RuleFlag(BaseModel):
    code: str
    severity: str
    title: str
    explain: str
    recommendation: str
    dataRefs: list[str]
    tags: list[str]


class RuleEval(BaseModel):
    overallSeverity: str
    isBatchEligible: bool
    flags: list[RuleFlag]


class WorklistItem(BaseModel):
    caseId: str
    patientRef: str
    serviceRequestRef: str
    status: str
    ownerSubject: str | None
    snapshotSummary: str
    ruleEval: RuleEval


class WorklistGroup(BaseModel):
    groupKey: str
    title: str
    count: int
    items: list[WorklistItem]


class WorklistResponse(BaseModel):
    groups: list[WorklistGroup]
