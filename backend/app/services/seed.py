from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import OrderCase


def seed_demo_cases(db: Session) -> None:
    existing = db.query(OrderCase).first()
    if existing:
        return

    now = datetime.now(timezone.utc).isoformat()

    def rule_eval(overall: str, is_batch_eligible: bool, flags: list[dict]) -> dict:
        return {
            "overallSeverity": overall,
            "isBatchEligible": is_batch_eligible,
            "flags": flags,
        }

    def make_case(
        patient_ref: str,
        service_request_ref: str,
        status: str,
        owner_subject: str | None,
        snapshot_summary: str,
        rule_eval_payload: dict,
    ) -> OrderCase:
        return OrderCase(
            id=str(uuid4()),
            patient_ref=patient_ref,
            service_request_ref=service_request_ref,
            status=status,
            owner_subject=owner_subject,
            snapshot_json=json.dumps({"summary": snapshot_summary}),
            local_facts_json="{}",
            draft_json=json.dumps(
                {
                    "examCode": "BONE_SCAN",
                    "radiopharmaceuticalCode": "local",
                    "suggestedDose": {"value": 185, "unit": "MBq"},
                    "override": {"isOverride": False, "reason": ""},
                    "ruleEval": rule_eval_payload,
                }
            ),
            final_fhir_medication_request_ref=None,
            created_at=now,
            updated_at=now,
        )

    warning_flag = {
        "code": "MISSING_WEIGHT",
        "severity": "WARN",
        "title": "Missing weight",
        "explain": "Weight is required for dose checks.",
        "recommendation": "Provide a recent weight measurement.",
        "dataRefs": [],
        "tags": ["dose"],
    }

    cases = [
        make_case(
            "Patient/001",
            "ServiceRequest/001",
            "NM_PENDING",
            None,
            "Patient 001",
            rule_eval("PASS", True, []),
        ),
        make_case(
            "Patient/002",
            "ServiceRequest/002",
            "RETURNED",
            None,
            "Patient 002",
            rule_eval("WARN", False, [warning_flag]),
        ),
        make_case(
            "Patient/003",
            "ServiceRequest/003",
            "NM_DRAFTED",
            None,
            "Patient 003",
            rule_eval("PASS", True, []),
        ),
        make_case(
            "Patient/004",
            "ServiceRequest/004",
            "PHARM_READY",
            None,
            "Patient 004",
            rule_eval("WARN", False, [warning_flag]),
        ),
        make_case(
            "Patient/005",
            "ServiceRequest/005",
            "PHARM_READY",
            None,
            "Patient 005",
            rule_eval("PASS", True, []),
        ),
        make_case(
            "Patient/006",
            "ServiceRequest/006",
            "PHARM_IN_PROGRESS",
            "demo-user",
            "Patient 006",
            rule_eval("PASS", True, []),
        ),
    ]

    db.add_all(cases)
    db.commit()
