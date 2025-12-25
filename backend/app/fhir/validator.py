from __future__ import annotations

import json
from typing import Any

from app.db.models import OrderCase
from app.fhir.mappers import load_catalog


def _parse_json(payload: str) -> dict[str, Any]:
    if not payload:
        return {}
    try:
        parsed = json.loads(payload)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def validate_case_for_approval(case: OrderCase) -> list[str]:
    errors: list[str] = []
    draft = _parse_json(case.draft_json)
    catalog = load_catalog()
    radiopharms = catalog.get("radiopharmaceuticals", {})

    if not case.patient_ref:
        errors.append("patientRef is required.")
    if not case.service_request_ref:
        errors.append("serviceRequestRef is required.")

    radiopharm_code = draft.get("radiopharmaceuticalCode") if isinstance(draft, dict) else None
    if not radiopharm_code:
        errors.append("radiopharmaceuticalCode is required.")
    elif radiopharm_code not in radiopharms:
        errors.append("radiopharmaceuticalCode is not in mapping catalog.")

    suggested = draft.get("suggestedDose") if isinstance(draft, dict) else None
    if not isinstance(suggested, dict):
        errors.append("suggestedDose is required.")
    else:
        value = suggested.get("value")
        unit = suggested.get("unit")
        if value is None or not isinstance(value, (int, float)):
            errors.append("suggestedDose.value must be numeric.")
        if not unit:
            errors.append("suggestedDose.unit is required.")

    return errors


def validate_medication_request(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("resourceType") != "MedicationRequest":
        errors.append("resourceType must be MedicationRequest.")
    if not payload.get("status"):
        errors.append("status is required.")
    if not payload.get("intent"):
        errors.append("intent is required.")
    subject = payload.get("subject", {})
    if not isinstance(subject, dict) or not subject.get("reference"):
        errors.append("subject.reference is required.")
    requester = payload.get("requester", {})
    if not isinstance(requester, dict) or not requester.get("reference"):
        errors.append("requester.reference is required.")
    if not payload.get("authoredOn"):
        errors.append("authoredOn is required.")

    medication = payload.get("medicationCodeableConcept", {})
    coding = medication.get("coding") if isinstance(medication, dict) else None
    if not isinstance(coding, list) or not coding:
        errors.append("medicationCodeableConcept.coding is required.")
    else:
        first = coding[0] if isinstance(coding[0], dict) else {}
        if not first.get("code") or not first.get("system"):
            errors.append("medicationCodeableConcept.coding[0].system/code is required.")

    dosage = payload.get("dosageInstruction")
    if not isinstance(dosage, list) or not dosage:
        errors.append("dosageInstruction is required.")
    else:
        dose_and_rate = dosage[0].get("doseAndRate") if isinstance(dosage[0], dict) else None
        if not isinstance(dose_and_rate, list) or not dose_and_rate:
            errors.append("dosageInstruction.doseAndRate is required.")
        else:
            quantity = dose_and_rate[0].get("doseQuantity") if isinstance(dose_and_rate[0], dict) else None
            if not isinstance(quantity, dict):
                errors.append("doseQuantity is required.")
            else:
                if quantity.get("value") is None:
                    errors.append("doseQuantity.value is required.")
                if not quantity.get("unit"):
                    errors.append("doseQuantity.unit is required.")

    identifiers = payload.get("identifier")
    if not isinstance(identifiers, list) or not identifiers:
        errors.append("identifier is required.")
    else:
        ident = identifiers[0] if isinstance(identifiers[0], dict) else {}
        if not ident.get("system") or not ident.get("value"):
            errors.append("identifier.system/value is required.")

    return errors
