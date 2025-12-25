from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import OrderCase, ReviewEvent
from app.rules.engine import evaluate as evaluate_rules
from app.schemas.snapshot import CandidateFact
from app.services.errors import error_response


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_json(payload: str) -> dict:
    if not payload:
        return {}
    try:
        parsed = json.loads(payload)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


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


def _apply_fact(
    local_facts: dict,
    fact: CandidateFact,
    actor_subject: str,
) -> None:
    entry = {
        "value": fact.value,
        "unit": fact.unit,
        "asOf": fact.asOf,
        "source": "AUTOFILL",
        "sourceType": fact.sourceType,
        "sourceRef": fact.sourceRef,
        "enteredBy": actor_subject,
    }

    if fact.factType == "WEIGHT_KG":
        local_facts["weightKg"] = entry
    elif fact.factType == "EGFR":
        renal = local_facts.setdefault("renal", {})
        renal["eGFR"] = entry
    elif fact.factType == "SCR_MGDL":
        renal = local_facts.setdefault("renal", {})
        renal["scrMgDl"] = entry
    elif fact.factType == "ALLERGY_SUMMARY":
        local_facts["allergySummary"] = entry


def accept_autofill(
    db: Session,
    case_id: str,
    facts: list[CandidateFact],
    reason: str | None,
    actor_subject: str,
    acting_role: str,
):
    case = db.query(OrderCase).filter(OrderCase.id == case_id).one_or_none()
    if not case:
        return error_response("NOT_FOUND", "Case not found.", 404)

    local_facts = _parse_json(case.local_facts_json)
    for fact in facts:
        _apply_fact(local_facts, fact, actor_subject)

    case.local_facts_json = json.dumps(local_facts)

    draft_payload = _parse_json(case.draft_json)
    rule_eval = evaluate_rules(case)
    if isinstance(draft_payload, dict):
        draft_payload["ruleEval"] = rule_eval
        case.draft_json = json.dumps(draft_payload)

    case.updated_at = _now_iso()

    _create_review_event(
        db,
        case.id,
        "AUTOFILL_ACCEPT",
        actor_subject,
        acting_role,
        {
            "facts": [fact.model_dump() for fact in facts],
            "reason": reason,
        },
    )
    db.commit()
    return {
        "caseId": case.id,
        "updatedLocalFacts": local_facts,
        "cds": rule_eval,
    }


def reject_autofill(
    db: Session,
    case_id: str,
    rejections: list[dict],
    actor_subject: str,
    acting_role: str,
):
    case = db.query(OrderCase).filter(OrderCase.id == case_id).one_or_none()
    if not case:
        return error_response("NOT_FOUND", "Case not found.", 404)

    snapshot = _parse_json(case.snapshot_json)
    existing = snapshot.get("autofillRejections")
    if not isinstance(existing, list):
        existing = []
    existing.extend(rejections)
    snapshot["autofillRejections"] = existing
    case.snapshot_json = json.dumps(snapshot)
    case.updated_at = _now_iso()

    _create_review_event(
        db,
        case.id,
        "AUTOFILL_REJECT",
        actor_subject,
        acting_role,
        {"rejections": rejections},
    )
    db.commit()
    return {"caseId": case.id, "rejected": True}
