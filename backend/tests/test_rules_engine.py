from __future__ import annotations

import json

from app.db.models import OrderCase
from app.rules.engine import evaluate


def _make_case(draft: dict, local_facts: dict | None = None, snapshot: dict | None = None) -> OrderCase:
    return OrderCase(
        id="case-1",
        patient_ref="Patient/1",
        service_request_ref="ServiceRequest/1",
        status="NM_DRAFTED",
        owner_subject=None,
        snapshot_json=json.dumps(snapshot or {}),
        local_facts_json=json.dumps(local_facts or {}),
        draft_json=json.dumps(draft),
        final_fhir_medication_request_ref=None,
        created_at="2025-01-01T00:00:00+00:00",
        updated_at="2025-01-01T00:00:00+00:00",
    )


def test_missing_weight_blocks_batch() -> None:
    case = _make_case(
        {
            "examCode": "BONE_SCAN",
            "radiopharmaceuticalCode": "LOCAL_BONE_01",
            "suggestedDose": {"value": 200, "unit": "MBq"},
            "override": {"isOverride": False, "reason": ""},
        }
    )
    result = evaluate(case)
    codes = {flag["code"] for flag in result["flags"]}
    assert "MISSING_WEIGHT" in codes
    assert result["isBatchEligible"] is False


def test_dose_out_of_range_flags_fail() -> None:
    case = _make_case(
        {
            "examCode": "BONE_SCAN",
            "radiopharmaceuticalCode": "LOCAL_BONE_01",
            "suggestedDose": {"value": 500, "unit": "MBq"},
            "override": {"isOverride": False, "reason": ""},
        },
        local_facts={"weightKg": {"value": 70, "source": "HIS"}},
    )
    result = evaluate(case)
    codes = {flag["code"] for flag in result["flags"]}
    assert "DOSE_OUT_OF_RANGE" in codes
    assert result["overallSeverity"] == "FAIL"


def test_override_requires_review_and_blocks_batch() -> None:
    case = _make_case(
        {
            "examCode": "BONE_SCAN",
            "radiopharmaceuticalCode": "LOCAL_BONE_01",
            "suggestedDose": {"value": 200, "unit": "MBq"},
            "override": {"isOverride": True, "reason": "Clinical override"},
        },
        local_facts={"weightKg": {"value": 70, "source": "HIS"}},
    )
    result = evaluate(case)
    codes = {flag["code"] for flag in result["flags"]}
    assert "OVERRIDE_REQUIRES_REVIEW" in codes
    assert result["isBatchEligible"] is False
