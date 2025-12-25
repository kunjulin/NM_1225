from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import OrderCase
from app.schemas.snapshot import CandidateFact
from app.services.errors import error_response


def _parse_json(payload: str) -> dict[str, Any]:
    if not payload:
        return {}
    try:
        parsed = json.loads(payload)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _collect_strings(payload: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(payload, str):
        strings.append(payload)
    elif isinstance(payload, dict):
        for value in payload.values():
            strings.extend(_collect_strings(value))
    elif isinstance(payload, list):
        for value in payload:
            strings.extend(_collect_strings(value))
    return strings


def _weight_candidate(
    snapshot: dict[str, Any],
    fallback_as_of: str,
) -> CandidateFact | None:
    weights = snapshot.get("weights")
    if isinstance(weights, list) and weights:
        entry = weights[-1] if isinstance(weights[-1], dict) else None
        if entry and entry.get("value") is not None:
            return CandidateFact(
                factType="WEIGHT_KG",
                value=entry.get("value"),
                unit=str(entry.get("unit") or "kg"),
                asOf=str(entry.get("asOf") or fallback_as_of),
                sourceType="LOCAL_SNAPSHOT",
                sourceRef=str(entry.get("sourceRef") or "snapshot_json"),
                sourceSnippet=None,
                confidence="HIGH",
                extractionMethod="STRUCTURED",
            )

    for text in _collect_strings(snapshot):
        match = re.search(r"weight[:\s]*([0-9]+(?:\.[0-9]+)?)\s*kg", text, re.I)
        if match:
            return CandidateFact(
                factType="WEIGHT_KG",
                value=float(match.group(1)),
                unit="kg",
                asOf=fallback_as_of,
                sourceType="DOCUMENT_TEXT",
                sourceRef="snapshot_json",
                sourceSnippet=match.group(0),
                confidence="MEDIUM",
                extractionMethod="PATTERN",
            )
    return None


def _renal_candidates(
    snapshot: dict[str, Any],
    fallback_as_of: str,
) -> list[CandidateFact]:
    candidates: list[CandidateFact] = []
    labs = snapshot.get("labs")
    if isinstance(labs, list):
        for entry in labs:
            if not isinstance(entry, dict):
                continue
            lab_type = str(entry.get("type") or "").upper()
            if lab_type in {"EGFR", "E_GFR"} and entry.get("value") is not None:
                candidates.append(
                    CandidateFact(
                        factType="EGFR",
                        value=entry.get("value"),
                        unit=str(entry.get("unit") or "mL/min/1.73m2"),
                        asOf=str(entry.get("asOf") or fallback_as_of),
                        sourceType="LOCAL_SNAPSHOT",
                        sourceRef=str(entry.get("sourceRef") or "snapshot_json"),
                        sourceSnippet=None,
                        confidence="HIGH",
                        extractionMethod="STRUCTURED",
                    )
                )
            if lab_type in {"SCR", "CREATININE", "S.CR"} and entry.get("value") is not None:
                candidates.append(
                    CandidateFact(
                        factType="SCR_MGDL",
                        value=entry.get("value"),
                        unit=str(entry.get("unit") or "mg/dL"),
                        asOf=str(entry.get("asOf") or fallback_as_of),
                        sourceType="LOCAL_SNAPSHOT",
                        sourceRef=str(entry.get("sourceRef") or "snapshot_json"),
                        sourceSnippet=None,
                        confidence="HIGH",
                        extractionMethod="STRUCTURED",
                    )
                )

    for text in _collect_strings(snapshot):
        egfr_match = re.search(r"eGFR[:\s]*([0-9]+(?:\.[0-9]+)?)", text, re.I)
        if egfr_match:
            candidates.append(
                CandidateFact(
                    factType="EGFR",
                    value=float(egfr_match.group(1)),
                    unit="mL/min/1.73m2",
                    asOf=fallback_as_of,
                    sourceType="DOCUMENT_TEXT",
                    sourceRef="snapshot_json",
                    sourceSnippet=egfr_match.group(0),
                    confidence="MEDIUM",
                    extractionMethod="PATTERN",
                )
            )
            break

    for text in _collect_strings(snapshot):
        scr_match = re.search(r"\b(?:CR|SCR|S\.CR)\b[:=]?\s*([0-9]+(?:\.[0-9]+)?)", text, re.I)
        if scr_match:
            candidates.append(
                CandidateFact(
                    factType="SCR_MGDL",
                    value=float(scr_match.group(1)),
                    unit="mg/dL",
                    asOf=fallback_as_of,
                    sourceType="DOCUMENT_TEXT",
                    sourceRef="snapshot_json",
                    sourceSnippet=scr_match.group(0),
                    confidence="MEDIUM",
                    extractionMethod="PATTERN",
                )
            )
            break

    return candidates


def _allergy_candidate(
    snapshot: dict[str, Any],
    fallback_as_of: str,
) -> CandidateFact | None:
    allergy_summary = snapshot.get("allergySummary")
    if isinstance(allergy_summary, dict):
        value = allergy_summary.get("value")
        if isinstance(value, str):
            return CandidateFact(
                factType="ALLERGY_SUMMARY",
                value=value,
                unit="",
                asOf=str(allergy_summary.get("asOf") or fallback_as_of),
                sourceType="LOCAL_SNAPSHOT",
                sourceRef=str(allergy_summary.get("sourceRef") or "snapshot_json"),
                sourceSnippet=None,
                confidence="HIGH",
                extractionMethod="STRUCTURED",
            )
    if isinstance(allergy_summary, str):
        return CandidateFact(
            factType="ALLERGY_SUMMARY",
            value=allergy_summary,
            unit="",
            asOf=fallback_as_of,
            sourceType="LOCAL_SNAPSHOT",
            sourceRef="snapshot_json",
            sourceSnippet=None,
            confidence="MEDIUM",
            extractionMethod="STRUCTURED",
        )

    for text in _collect_strings(snapshot):
        if "NKDA" in text.upper():
            return CandidateFact(
                factType="ALLERGY_SUMMARY",
                value="NKDA",
                unit="",
                asOf=fallback_as_of,
                sourceType="DOCUMENT_TEXT",
                sourceRef="snapshot_json",
                sourceSnippet="NKDA",
                confidence="MEDIUM",
                extractionMethod="PATTERN",
            )
        match = re.search(r"allergy[:\s]*(.+)", text, re.I)
        if match:
            return CandidateFact(
                factType="ALLERGY_SUMMARY",
                value=match.group(1).strip(),
                unit="",
                asOf=fallback_as_of,
                sourceType="DOCUMENT_TEXT",
                sourceRef="snapshot_json",
                sourceSnippet=match.group(0),
                confidence="LOW",
                extractionMethod="PATTERN",
            )
    return None


def get_snapshot(db: Session, case_id: str, refresh: bool):
    case = db.query(OrderCase).filter(OrderCase.id == case_id).one_or_none()
    if not case:
        return error_response("NOT_FOUND", "Case not found.", 404)

    snapshot = _parse_json(case.snapshot_json)
    fallback_as_of = case.updated_at

    candidates: list[CandidateFact] = []
    weight_candidate = _weight_candidate(snapshot, fallback_as_of)
    if weight_candidate:
        candidates.append(weight_candidate)
    candidates.extend(_renal_candidates(snapshot, fallback_as_of))
    allergy_candidate = _allergy_candidate(snapshot, fallback_as_of)
    if allergy_candidate:
        candidates.append(allergy_candidate)

    if refresh:
        # TODO: Replace with HIS/FHIR retrieval when available.
        pass

    return {
        "caseId": case.id,
        "patientRef": case.patient_ref,
        "serviceRequestRef": case.service_request_ref,
        "snapshot": snapshot,
        "candidateFacts": candidates,
    }
