from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.db.models import OrderCase


_CATALOG_CACHE: dict[str, Any] | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_json(payload: str) -> dict[str, Any]:
    if not payload:
        return {}
    try:
        parsed = json.loads(payload)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def load_catalog() -> dict[str, Any]:
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None:
        return _CATALOG_CACHE
    path = Path(__file__).resolve().parents[1] / "mapping" / "catalog.yaml"
    with path.open("r", encoding="utf-8") as handle:
        _CATALOG_CACHE = yaml.safe_load(handle) or {}
    return _CATALOG_CACHE


def _ucum_code(unit: str | None) -> str | None:
    if not unit:
        return None
    unit_norm = unit.strip()
    if unit_norm.upper() == "MBQ":
        return "MBq"
    return None


def map_medication_request(case: OrderCase) -> dict[str, Any]:
    catalog = load_catalog()
    draft = _parse_json(case.draft_json)

    exam_code = draft.get("examCode")
    radiopharm_code = draft.get("radiopharmaceuticalCode")
    suggested_dose = draft.get("suggestedDose") if isinstance(draft, dict) else {}
    override = draft.get("override") if isinstance(draft, dict) else {}
    rule_eval = draft.get("ruleEval") if isinstance(draft, dict) else {}

    radiopharms = catalog.get("radiopharmaceuticals", {})
    radiopharm = radiopharms.get(radiopharm_code, {}) if radiopharm_code else {}
    radiopharm_system = radiopharm.get("system") or "http://example.org/local/radiopharm"
    radiopharm_display = radiopharm.get("display") or radiopharm_code or "Unknown"

    procedures = catalog.get("procedures", {})
    procedure = procedures.get(exam_code, {}) if exam_code else {}

    requester_org = catalog.get("organizations", {}).get("requesterOrganization", {})
    requester_practitioner = catalog.get("practitioners", {}).get("defaultRequester", {})
    requester = requester_practitioner or requester_org or {"reference": "Organization/demo"}

    unit = suggested_dose.get("unit") if isinstance(suggested_dose, dict) else None
    ucum_code = _ucum_code(unit)

    medication_request: dict[str, Any] = {
        "resourceType": "MedicationRequest",
        "status": "active",
        "intent": "order",
        "subject": {"reference": case.patient_ref},
        "authoredOn": _now_iso(),
        "requester": requester,
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": radiopharm_system,
                    "code": radiopharm_code or "UNKNOWN",
                    "display": radiopharm_display,
                }
            ],
            "text": radiopharm_display,
        },
        "dosageInstruction": [
            {
                "doseAndRate": [
                    {
                        "doseQuantity": {
                            "value": suggested_dose.get("value"),
                            "unit": unit,
                        }
                    }
                ]
            }
        ],
        "identifier": [
            {
                "system": "http://example.org/nm-stewardship/caseId",
                "value": case.id,
            }
        ],
    }

    if ucum_code:
        medication_request["dosageInstruction"][0]["doseAndRate"][0]["doseQuantity"][
            "system"
        ] = "http://unitsofmeasure.org"
        medication_request["dosageInstruction"][0]["doseAndRate"][0]["doseQuantity"][
            "code"
        ] = ucum_code

    if case.service_request_ref:
        medication_request["basedOn"] = [{"reference": case.service_request_ref}]
        medication_request["reasonReference"] = [{"reference": case.service_request_ref}]

    notes = []
    if isinstance(override, dict) and override.get("isOverride"):
        notes.append("Override requested.")
    if isinstance(rule_eval, dict):
        flags = rule_eval.get("flags", [])
        if isinstance(flags, list) and flags:
            codes = [flag.get("code") for flag in flags if isinstance(flag, dict)]
            notes.append("Flags: " + ", ".join([code for code in codes if code]))
    if notes:
        medication_request["note"] = [{"text": " ".join(notes)}]

    extensions = []
    if procedure:
        # TODO: Replace example extension URL with TW Core canonical when confirmed.
        extensions.append(
            {
                "url": "http://example.org/fhir/StructureDefinition/exam-code",
                "valueCodeableConcept": {
                    "coding": [
                        {
                            "system": procedure.get("system"),
                            "code": exam_code,
                            "display": procedure.get("display"),
                        }
                    ],
                    "text": procedure.get("display"),
                },
            }
        )
    # TODO: Replace example extension URL with TW Core canonical when confirmed.
    extensions.append(
        {
            "url": "http://example.org/fhir/StructureDefinition/internal-case-id",
            "valueString": case.id,
        }
    )
    if extensions:
        medication_request["extension"] = extensions

    return medication_request
