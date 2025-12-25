from __future__ import annotations

import json

from app.db.models import OrderCase
from app.fhir.mappers import map_medication_request
from app.fhir.validator import validate_case_for_approval


def _make_case(draft: dict) -> OrderCase:
    return OrderCase(
        id="case-1",
        patient_ref="Patient/1",
        service_request_ref="ServiceRequest/1",
        status="APPROVED",
        owner_subject=None,
        snapshot_json="{}",
        local_facts_json="{}",
        draft_json=json.dumps(draft),
        final_fhir_medication_request_ref=None,
        created_at="2025-01-01T00:00:00+00:00",
        updated_at="2025-01-01T00:00:00+00:00",
    )


def test_mapper_required_fields() -> None:
    case = _make_case(
        {
            "examCode": "BONE_SCAN",
            "radiopharmaceuticalCode": "LOCAL_BONE_01",
            "suggestedDose": {"value": 200, "unit": "MBq"},
            "override": {"isOverride": False, "reason": ""},
        }
    )
    payload = map_medication_request(case)
    assert payload["resourceType"] == "MedicationRequest"
    assert payload["status"] == "active"
    assert payload["intent"] == "order"
    assert payload["subject"]["reference"] == "Patient/1"
    assert payload["requester"]["reference"]
    coding = payload["medicationCodeableConcept"]["coding"][0]
    assert coding["code"] == "LOCAL_BONE_01"
    assert coding["system"]
    quantity = payload["dosageInstruction"][0]["doseAndRate"][0]["doseQuantity"]
    assert quantity["value"] == 200
    assert quantity["unit"] == "MBq"
    assert payload["identifier"][0]["value"] == "case-1"


def test_mapping_radiopharm_lookup() -> None:
    case = _make_case(
        {
            "examCode": "BONE_SCAN",
            "radiopharmaceuticalCode": "LOCAL_BONE_01",
            "suggestedDose": {"value": 200, "unit": "MBq"},
            "override": {"isOverride": False, "reason": ""},
        }
    )
    payload = map_medication_request(case)
    coding = payload["medicationCodeableConcept"]["coding"][0]
    assert coding["code"] == "LOCAL_BONE_01"


def test_validator_rejects_missing_dose_or_medication() -> None:
    case_missing_dose = _make_case(
        {
            "examCode": "BONE_SCAN",
            "radiopharmaceuticalCode": "LOCAL_BONE_01",
            "override": {"isOverride": False, "reason": ""},
        }
    )
    errors = validate_case_for_approval(case_missing_dose)
    assert any("suggestedDose" in error for error in errors)

    case_missing_med = _make_case(
        {
            "examCode": "BONE_SCAN",
            "suggestedDose": {"value": 200, "unit": "MBq"},
            "override": {"isOverride": False, "reason": ""},
        }
    )
    errors = validate_case_for_approval(case_missing_med)
    assert any("radiopharmaceuticalCode" in error for error in errors)
