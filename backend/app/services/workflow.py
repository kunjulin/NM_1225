from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import OrderCase, Outbox, ReviewEvent
from app.schemas.workflow import BulkApproveResponse, BulkFailure, CaseStatus
from app.services.errors import error_response
from app.fhir.validator import validate_case_for_approval
from app.rules.engine import evaluate as evaluate_rules
from app.services.worklist import build_worklist_item


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _create_review_event(
    db: Session,
    case_id: str,
    event_type: str,
    actor_subject: str,
    acting_role: str,
    payload: dict,
) -> None:
    event = ReviewEvent(
        id=str(uuid4()),
        case_id=case_id,
        event_type=event_type,
        actor_subject=actor_subject,
        acting_role=acting_role,
        payload_json=json.dumps(payload),
        created_at=_now_iso(),
    )
    db.add(event)


def _create_outbox(db: Session, case_id: str) -> None:
    now = _now_iso()
    outbox = Outbox(
        id=str(uuid4()),
        case_id=case_id,
        operation="CREATE_MEDICATION_REQUEST",
        request_json=json.dumps({"caseId": case_id}),
        status="PENDING",
        last_error=None,
        retry_count=0,
        next_retry_at=None,
        created_at=now,
        updated_at=now,
    )
    db.add(outbox)


def _get_case(db: Session, case_id: str) -> OrderCase | None:
    return db.query(OrderCase).filter(OrderCase.id == case_id).one_or_none()


def update_draft(
    db: Session,
    case_id: str,
    draft_payload: dict,
    actor_subject: str,
    acting_role: str,
):
    case = _get_case(db, case_id)
    if not case:
        return error_response("NOT_FOUND", "Case not found.", 404)
    if case.status not in {"NM_PENDING", "RETURNED", "NM_DRAFTED"}:
        return error_response("INVALID_STATE", "Draft not allowed in current state.", 409)

    case.draft_json = json.dumps(draft_payload)
    rule_eval = evaluate_rules(case)
    draft_payload["ruleEval"] = rule_eval

    now = _now_iso()
    case.draft_json = json.dumps(draft_payload)
    case.status = "NM_DRAFTED"
    case.updated_at = now

    _create_review_event(
        db,
        case.id,
        "DRAFT_UPDATE",
        actor_subject,
        acting_role,
        {"draft": draft_payload},
    )

    db.commit()
    db.refresh(case)
    return build_worklist_item(case)


def submit_case(
    db: Session,
    case_id: str,
    actor_subject: str,
    acting_role: str,
):
    case = _get_case(db, case_id)
    if not case:
        return error_response("NOT_FOUND", "Case not found.", 404)
    if case.status != "NM_DRAFTED":
        return error_response("INVALID_STATE", "Submit not allowed in current state.", 409)

    now = _now_iso()
    case.status = "PHARM_READY"
    case.owner_subject = None
    case.updated_at = now

    _create_review_event(
        db,
        case.id,
        "SUBMIT",
        actor_subject,
        acting_role,
        {},
    )
    db.commit()
    return {"caseId": case.id, "status": case.status}


def respond_case(
    db: Session,
    case_id: str,
    response_action: str,
    comment: str | None,
    actor_subject: str,
    acting_role: str,
):
    case = _get_case(db, case_id)
    if not case:
        return error_response("NOT_FOUND", "Case not found.", 404)
    if case.status != "RETURNED":
        return error_response("INVALID_STATE", "Response not allowed in current state.", 409)

    now = _now_iso()
    case.status = "NM_DRAFTED"
    case.updated_at = now

    _create_review_event(
        db,
        case.id,
        "RESPONSE",
        actor_subject,
        acting_role,
        {"responseAction": response_action, "comment": comment},
    )
    db.commit()
    return {"caseId": case.id, "status": case.status}


def claim_case(
    db: Session,
    case_id: str,
    actor_subject: str,
    acting_role: str,
):
    now = _now_iso()
    updated = (
        db.query(OrderCase)
        .filter(OrderCase.id == case_id, OrderCase.status == "PHARM_READY")
        .update(
            {
                "status": "PHARM_IN_PROGRESS",
                "owner_subject": actor_subject,
                "updated_at": now,
            }
        )
    )
    if updated == 0:
        case = _get_case(db, case_id)
        if not case:
            return error_response("NOT_FOUND", "Case not found.", 404)
        return error_response("INVALID_STATE", "Claim not allowed in current state.", 409)

    _create_review_event(
        db,
        case_id,
        "CLAIM",
        actor_subject,
        acting_role,
        {},
    )
    db.commit()
    case = _get_case(db, case_id)
    return {
        "caseId": case.id,
        "status": case.status,
        "ownerSubject": case.owner_subject,
    }


def approve_case(
    db: Session,
    case_id: str,
    actor_subject: str,
    acting_role: str,
):
    case = _get_case(db, case_id)
    if not case:
        return error_response("NOT_FOUND", "Case not found.", 404)
    if case.status == "PHARM_READY":
        validation_errors = validate_case_for_approval(case)
        if validation_errors:
            return error_response(
                "VALIDATION_ERROR",
                "Case failed approval validation.",
                422,
                {"errors": validation_errors},
            )
        now = _now_iso()
        updated = (
            db.query(OrderCase)
            .filter(OrderCase.id == case_id, OrderCase.status == "PHARM_READY")
            .update(
                {
                    "status": "PHARM_IN_PROGRESS",
                    "owner_subject": actor_subject,
                    "updated_at": now,
                }
            )
        )
        if updated == 0:
            return error_response("INVALID_STATE", "Approve not allowed in current state.", 409)
        _create_review_event(
            db,
            case_id,
            "CLAIM",
            actor_subject,
            acting_role,
            {"autoClaimed": True},
        )
    elif case.status == "PHARM_IN_PROGRESS":
        if case.owner_subject != actor_subject:
            return error_response("NOT_OWNER", "Case is owned by another user.", 403)
        validation_errors = validate_case_for_approval(case)
        if validation_errors:
            return error_response(
                "VALIDATION_ERROR",
                "Case failed approval validation.",
                422,
                {"errors": validation_errors},
            )
    else:
        return error_response("INVALID_STATE", "Approve not allowed in current state.", 409)

    now = _now_iso()
    case = _get_case(db, case_id)
    if not case:
        return error_response("NOT_FOUND", "Case not found.", 404)
    case.status = "APPROVED"
    case.updated_at = now

    _create_review_event(
        db,
        case.id,
        "APPROVE",
        actor_subject,
        acting_role,
        {},
    )
    _create_outbox(db, case.id)
    db.commit()
    return {"caseId": case.id, "status": case.status}


def return_case(
    db: Session,
    case_id: str,
    reasons: list[str],
    comment: str | None,
    actor_subject: str,
    acting_role: str,
):
    case = _get_case(db, case_id)
    if not case:
        return error_response("NOT_FOUND", "Case not found.", 404)
    if case.status not in {"PHARM_READY", "PHARM_IN_PROGRESS"}:
        return error_response("INVALID_STATE", "Return not allowed in current state.", 409)
    if case.status == "PHARM_IN_PROGRESS" and case.owner_subject != actor_subject:
        return error_response("NOT_OWNER", "Case is owned by another user.", 403)

    now = _now_iso()
    case.status = "RETURNED"
    case.owner_subject = None
    case.updated_at = now

    _create_review_event(
        db,
        case.id,
        "RETURN",
        actor_subject,
        acting_role,
        {"returnReasonCodes": reasons, "comment": comment},
    )
    db.commit()
    return {"caseId": case.id, "status": case.status}


def bulk_approve(
    db: Session,
    case_ids: list[str],
    note: str | None,
    actor_subject: str,
    acting_role: str,
) -> BulkApproveResponse:
    ok: list[CaseStatus] = []
    failed: list[BulkFailure] = []

    for case_id in case_ids:
        case = _get_case(db, case_id)
        if not case:
            failed.append(
                BulkFailure(
                    caseId=case_id,
                    code="NOT_FOUND",
                    message="Case not found.",
                )
            )
            continue

        rule_eval = evaluate_rules(case)
        has_fail = any(flag.get("severity") == "FAIL" for flag in rule_eval.get("flags", []))
        if rule_eval.get("overallSeverity") == "FAIL" or has_fail:
            failed.append(
                BulkFailure(
                    caseId=case_id,
                    code="HAS_FAIL_FLAGS",
                    message="Case has FAIL rule flags.",
                )
            )
            continue
        if not rule_eval.get("isBatchEligible"):
            failed.append(
                BulkFailure(
                    caseId=case_id,
                    code="NOT_BATCH_ELIGIBLE",
                    message="Case is not batch eligible.",
                )
            )
            continue

        validation_errors = validate_case_for_approval(case)
        if validation_errors:
            failed.append(
                BulkFailure(
                    caseId=case_id,
                    code="VALIDATION_ERROR",
                    message="; ".join(validation_errors),
                )
            )
            continue

        if case.status == "PHARM_READY":
            now = _now_iso()
            updated = (
                db.query(OrderCase)
                .filter(OrderCase.id == case_id, OrderCase.status == "PHARM_READY")
                .update(
                    {
                        "status": "PHARM_IN_PROGRESS",
                        "owner_subject": actor_subject,
                        "updated_at": now,
                    }
                )
            )
            if updated == 0:
                failed.append(
                    BulkFailure(
                        caseId=case_id,
                        code="INVALID_STATE",
                        message="Approve not allowed in current state.",
                    )
                )
                continue
            _create_review_event(
                db,
                case.id,
                "CLAIM",
                actor_subject,
                acting_role,
                {"autoClaimed": True, "note": note},
            )
        elif case.status == "PHARM_IN_PROGRESS":
            if case.owner_subject != actor_subject:
                failed.append(
                    BulkFailure(
                        caseId=case_id,
                        code="NOT_OWNER",
                        message="Case is owned by another user.",
                    )
                )
                continue
        else:
            failed.append(
                BulkFailure(
                    caseId=case_id,
                    code="INVALID_STATE",
                    message="Approve not allowed in current state.",
                )
            )
            continue

        case = _get_case(db, case_id)
        if not case:
            failed.append(
                BulkFailure(
                    caseId=case_id,
                    code="NOT_FOUND",
                    message="Case not found.",
                )
            )
            continue
        now = _now_iso()
        case.status = "APPROVED"
        case.updated_at = now

        _create_review_event(
            db,
            case.id,
            "APPROVE",
            actor_subject,
            acting_role,
            {"note": note} if note else {},
        )
        _create_outbox(db, case.id)
        db.commit()
        ok.append(CaseStatus(caseId=case.id, status=case.status))

    return BulkApproveResponse(ok=ok, failed=failed)
