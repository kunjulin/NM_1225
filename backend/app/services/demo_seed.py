from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import OrderCase, Outbox, ReviewEvent
from app.rules.engine import evaluate as evaluate_rules


DEMO_CASE_IDS = [
    "demo-case-A",
    "demo-case-B",
    "demo-case-C",
    "demo-case-D",
    "demo-case-E",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _create_review_event(
    db: Session,
    case_id: str,
    actor_subject: str,
    acting_role: str,
    payload: dict,
) -> None:
    event = ReviewEvent(
        id=str(uuid4()),
        case_id=case_id,
        event_type="DEMO_SEED",
        actor_subject=actor_subject,
        acting_role=acting_role,
        payload_json=json.dumps(payload),
        created_at=_now_iso(),
    )
    db.add(event)


def _base_case(
    case_id: str,
    patient_ref: str,
    service_request_ref: str,
    status: str,
    snapshot: dict,
    local_facts: dict,
    draft: dict,
    now: str,
) -> OrderCase:
    return OrderCase(
        id=case_id,
        patient_ref=patient_ref,
        service_request_ref=service_request_ref,
        status=status,
        owner_subject=None,
        snapshot_json=json.dumps(snapshot),
        local_facts_json=json.dumps(local_facts),
        draft_json=json.dumps(draft),
        final_fhir_medication_request_ref=None,
        created_at=now,
        updated_at=now,
    )


def seed_demo_cases(
    db: Session,
    actor_subject: str,
    acting_role: str,
) -> dict:
    db.query(ReviewEvent).filter(ReviewEvent.case_id.in_(DEMO_CASE_IDS)).delete(
        synchronize_session=False
    )
    db.query(Outbox).filter(Outbox.case_id.in_(DEMO_CASE_IDS)).delete(
        synchronize_session=False
    )
    db.query(OrderCase).filter(OrderCase.id.in_(DEMO_CASE_IDS)).delete(
        synchronize_session=False
    )

    now = _now_iso()

    cases = [
        # Case A: Adult standard bone scan, PHARM_READY, within range.
        _base_case(
            "demo-case-A",
            "Patient/demo-A",
            "ServiceRequest/demo-A",
            "PHARM_READY",
            snapshot={
                "summary": "Adult bone scan candidate",
                "weights": [
                    {"value": 70, "unit": "kg", "asOf": now, "sourceRef": "Observation/demo-A"}
                ],
            },
            local_facts={
                "weightKg": {
                    "value": 70,
                    "unit": "kg",
                    "asOf": now,
                    "source": "HIS",
                    "sourceRef": "Observation/demo-A",
                }
            },
            draft={
                "examCode": "BONE_SCAN",
                "radiopharmaceuticalCode": "LOCAL_BONE_01",
                "suggestedDose": {"value": 200, "unit": "MBq"},
                "override": {"isOverride": False, "reason": ""},
            },
            now=now,
        ),
        # Case B: Pediatric exam requiring weight, NM_PENDING, missing local facts.
        _base_case(
            "demo-case-B",
            "Patient/demo-B",
            "ServiceRequest/demo-B",
            "NM_PENDING",
            snapshot={
                "summary": "Pediatric case with weight available",
                "weights": [
                    {"value": 25, "unit": "kg", "asOf": now, "sourceRef": "Observation/demo-B"}
                ],
            },
            local_facts={},
            draft={
                "examCode": "DMSA",
                "radiopharmaceuticalCode": "LOCAL_DMSA_01",
                "suggestedDose": {"value": 90, "unit": "MBq"},
                "override": {"isOverride": False, "reason": ""},
            },
            now=now,
        ),
        # Case C: Renal impairment case with renal facts.
        _base_case(
            "demo-case-C",
            "Patient/demo-C",
            "ServiceRequest/demo-C",
            "NM_DRAFTED",
            snapshot={
                "summary": "Renal impairment with eGFR data",
                "labs": [
                    {
                        "type": "eGFR",
                        "value": 45,
                        "unit": "mL/min/1.73m2",
                        "asOf": now,
                        "sourceRef": "Observation/demo-C",
                    }
                ],
            },
            local_facts={
                "weightKg": {
                    "value": 60,
                    "unit": "kg",
                    "asOf": now,
                    "source": "HIS",
                    "sourceRef": "Observation/demo-C",
                },
                "renal": {
                    "eGFR": {
                        "value": 45,
                        "unit": "mL/min/1.73m2",
                        "asOf": now,
                        "source": "HIS",
                        "sourceRef": "Observation/demo-C",
                    }
                },
            },
            draft={
                "examCode": "MAG3",
                "radiopharmaceuticalCode": "LOCAL_MAG3_01",
                "suggestedDose": {"value": 120, "unit": "MBq"},
                "override": {"isOverride": False, "reason": ""},
            },
            now=now,
        ),
        # Case D: Missing weight core demo.
        _base_case(
            "demo-case-D",
            "Patient/demo-D",
            "ServiceRequest/demo-D",
            "NM_PENDING",
            snapshot={
                "summary": "Weight: 62 kg",
                "notes": "Weight: 62 kg recorded in intake form.",
            },
            local_facts={},
            draft={
                "examCode": "BONE_SCAN",
                "radiopharmaceuticalCode": "LOCAL_BONE_01",
                "suggestedDose": {"value": 180, "unit": "MBq"},
                "override": {"isOverride": False, "reason": ""},
            },
            now=now,
        ),
        # Case E: Dose out-of-range.
        _base_case(
            "demo-case-E",
            "Patient/demo-E",
            "ServiceRequest/demo-E",
            "PHARM_READY",
            snapshot={
                "summary": "Dose out-of-range example",
                "weights": [
                    {"value": 68, "unit": "kg", "asOf": now, "sourceRef": "Observation/demo-E"}
                ],
            },
            local_facts={
                "weightKg": {
                    "value": 68,
                    "unit": "kg",
                    "asOf": now,
                    "source": "HIS",
                    "sourceRef": "Observation/demo-E",
                }
            },
            draft={
                "examCode": "BONE_SCAN",
                "radiopharmaceuticalCode": "LOCAL_BONE_01",
                "suggestedDose": {"value": 500, "unit": "MBq"},
                "override": {"isOverride": False, "reason": ""},
            },
            now=now,
        ),
    ]

    for case in cases:
        rule_eval = evaluate_rules(case)
        draft_payload = json.loads(case.draft_json)
        draft_payload["ruleEval"] = rule_eval
        case.draft_json = json.dumps(draft_payload)
        db.add(case)

    for case_id in DEMO_CASE_IDS:
        _create_review_event(
            db,
            case_id,
            actor_subject,
            acting_role,
            {"note": "demo seed"},
        )

    db.commit()
    return {"count": len(cases), "caseIds": DEMO_CASE_IDS}
