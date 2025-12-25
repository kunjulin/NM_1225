from __future__ import annotations

from typing import Iterable

from sqlalchemy.orm import Session

from app.db.models import OrderCase
import json

from app.schemas.worklist import WorklistGroup, WorklistItem, WorklistResponse
from app.rules.engine import evaluate as evaluate_rules


def _parse_snapshot_summary(snapshot_json: str) -> str:
    if not snapshot_json:
        return ""
    try:
        payload = json.loads(snapshot_json)
    except json.JSONDecodeError:
        return ""
    if isinstance(payload, dict) and isinstance(payload.get("summary"), str):
        return payload["summary"]
    return ""


def build_worklist_item(case: OrderCase) -> WorklistItem:
    return WorklistItem(
        caseId=case.id,
        patientRef=case.patient_ref,
        serviceRequestRef=case.service_request_ref,
        status=case.status,
        ownerSubject=case.owner_subject,
        snapshotSummary=_parse_snapshot_summary(case.snapshot_json),
        ruleEval=evaluate_rules(case),
    )


def get_nm_worklist(db: Session, statuses: Iterable[str] | None) -> WorklistResponse:
    status_list = list(statuses) if statuses else [
        "NM_PENDING",
        "RETURNED",
        "NM_DRAFTED",
    ]
    cases = (
        db.query(OrderCase)
        .filter(OrderCase.status.in_(status_list))
        .all()
    )
    items_by_status: dict[str, list[WorklistItem]] = {status: [] for status in status_list}
    for case in cases:
        items_by_status.setdefault(case.status, []).append(build_worklist_item(case))
    groups = [
        WorklistGroup(
            groupKey=status,
            title=status,
            count=len(items_by_status.get(status, [])),
            items=items_by_status.get(status, []),
        )
        for status in status_list
    ]
    return WorklistResponse(groups=groups)


def get_pharmacy_worklist(
    db: Session,
    statuses: Iterable[str] | None,
    login_subject: str,
) -> WorklistResponse:
    status_list = list(statuses) if statuses else [
        "PHARM_READY",
        "PHARM_IN_PROGRESS",
    ]
    cases = (
        db.query(OrderCase)
        .filter(OrderCase.status.in_(status_list))
        .all()
    )
    items = [build_worklist_item(case) for case in cases]
    exceptions: list[WorklistItem] = []
    batch_eligible: list[WorklistItem] = []
    my_claimed: list[WorklistItem] = []

    for item in items:
        has_warn_or_fail = any(
            flag.severity in {"WARN", "FAIL"} for flag in item.ruleEval.flags
        )
        has_fail = any(flag.severity == "FAIL" for flag in item.ruleEval.flags)

        if item.ownerSubject == login_subject:
            my_claimed.append(item)
        if (not item.ruleEval.isBatchEligible) or has_warn_or_fail:
            exceptions.append(item)
        if item.ruleEval.isBatchEligible and not has_fail:
            batch_eligible.append(item)

    groups = [
        WorklistGroup(
            groupKey="exceptions",
            title="exceptions",
            count=len(exceptions),
            items=exceptions,
        ),
        WorklistGroup(
            groupKey="batchEligible",
            title="batchEligible",
            count=len(batch_eligible),
            items=batch_eligible,
        ),
        WorklistGroup(
            groupKey="myClaimed",
            title="myClaimed",
            count=len(my_claimed),
            items=my_claimed,
        ),
    ]
    return WorklistResponse(groups=groups)
