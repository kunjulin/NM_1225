from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from app.db.models import OrderCase


_CONFIG_CACHE: dict[str, Any] | None = None


def _config_path() -> Path:
    return Path(__file__).resolve().parent / "rules_config.yaml"


def _load_config() -> dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    with _config_path().open("r", encoding="utf-8") as handle:
        _CONFIG_CACHE = yaml.safe_load(handle) or {}
    return _CONFIG_CACHE


def _parse_json(payload: str) -> Any:
    if not payload:
        return {}
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return {}


def _extract_weight(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key in ("weightKg", "weight"):
            value = payload.get(key)
            if isinstance(value, dict) and value.get("value") is not None:
                return True
            if isinstance(value, (int, float)):
                return True
        weights = payload.get("weights")
        if isinstance(weights, list):
            for entry in weights:
                if isinstance(entry, dict) and entry.get("value") is not None:
                    return True
        summary = payload.get("summary")
        if isinstance(summary, str) and "kg" in summary.lower():
            return True
    return False


def _extract_renal(payload: Any) -> bool:
    if isinstance(payload, dict):
        renal = payload.get("renal")
        if isinstance(renal, dict):
            egfr = renal.get("eGFR")
            if isinstance(egfr, dict) and egfr.get("value") is not None:
                return True
            if isinstance(egfr, (int, float)):
                return True
        egfr_direct = payload.get("eGFR")
        if isinstance(egfr_direct, dict) and egfr_direct.get("value") is not None:
            return True
        if isinstance(egfr_direct, (int, float)):
            return True
        summary = payload.get("summary")
        if isinstance(summary, str) and "egfr" in summary.lower():
            return True
    return False


def _extract_allergy_text(payload: Any) -> str | None:
    if isinstance(payload, dict):
        allergy = payload.get("allergySummary")
        if isinstance(allergy, dict):
            value = allergy.get("value")
            if isinstance(value, str):
                return value
        if isinstance(allergy, str):
            return allergy
        summary = payload.get("summary")
        if isinstance(summary, str) and "allergy" in summary.lower():
            return summary
    return None


def _has_local_data(payload: Any) -> bool:
    if isinstance(payload, dict):
        source = payload.get("source")
        if isinstance(source, str) and source in {"MANUAL", "AUTOFILL"}:
            return True
        for value in payload.values():
            if _has_local_data(value):
                return True
    if isinstance(payload, list):
        for entry in payload:
            if _has_local_data(entry):
                return True
    return False


def _severity_rank(severity: str) -> int:
    return {"PASS": 0, "INFO": 1, "WARN": 2, "FAIL": 3}.get(severity, 0)


def _flag(
    code: str,
    severity: str,
    title: str,
    explain: str,
    recommendation: str,
    data_refs: list[str] | None = None,
    tags: list[str] | None = None,
) -> dict:
    return {
        "code": code,
        "severity": severity,
        "title": title,
        "explain": explain,
        "recommendation": recommendation,
        "dataRefs": data_refs or [],
        "tags": tags or [],
    }


def evaluate(case: OrderCase) -> dict:
    config = _load_config()
    exams = config.get("exams", {}) if isinstance(config, dict) else {}

    draft_payload = _parse_json(case.draft_json)
    local_facts = _parse_json(case.local_facts_json)
    snapshot = _parse_json(case.snapshot_json)

    exam_code = draft_payload.get("examCode") if isinstance(draft_payload, dict) else None
    exam_cfg = exams.get(exam_code, {}) if isinstance(exams, dict) else {}

    allowed_codes = exam_cfg.get("allowedRadiopharmaceuticalCodes", []) if isinstance(exam_cfg, dict) else []
    required_facts = exam_cfg.get("requiredFacts", []) if isinstance(exam_cfg, dict) else []
    dose_policy = exam_cfg.get("dosePolicy", {}) if isinstance(exam_cfg, dict) else {}

    flags: list[dict] = []

    has_weight_local = _extract_weight(local_facts)
    has_renal_local = _extract_renal(local_facts)

    if "WEIGHT_KG" in required_facts and not has_weight_local:
        flags.append(
            _flag(
                "MISSING_WEIGHT",
                "FAIL",
                "Missing weight",
                "Weight is required for dose checks.",
                "Provide a recent weight measurement.",
                tags=["dose"],
            )
        )

    if "RENAL_FUNCTION" in required_facts and not has_renal_local:
        flags.append(
            _flag(
                "MISSING_RENAL_FUNCTION",
                "FAIL",
                "Missing renal function",
                "Renal function is required for dosing.",
                "Provide a recent eGFR or renal lab.",
                tags=["renal"],
            )
        )

    allergy_text = _extract_allergy_text(local_facts) or _extract_allergy_text(snapshot)
    if not allergy_text:
        flags.append(
            _flag(
                "ALLERGY_REVIEW_REQUIRED",
                "WARN",
                "Allergy review required",
                "Allergy history is missing.",
                "Confirm allergy history before approval.",
                tags=["allergy"],
            )
        )
    elif any(keyword in allergy_text.lower() for keyword in ("contrast", "radiopharm")):
        flags.append(
            _flag(
                "ALLERGY_REVIEW_REQUIRED",
                "WARN",
                "Allergy review required",
                "Allergy history indicates a contrast concern.",
                "Review allergy details before approval.",
                tags=["allergy"],
            )
        )

    if _has_local_data(local_facts):
        flags.append(
            _flag(
                "LOCAL_DATA_USED",
                "INFO",
                "Local data used",
                "Local facts were entered manually or via autofill.",
                "Verify local facts if needed.",
                tags=["demo"],
            )
        )

    radiopharm = draft_payload.get("radiopharmaceuticalCode") if isinstance(draft_payload, dict) else None
    if exam_code and radiopharm and allowed_codes and radiopharm not in allowed_codes:
        flags.append(
            _flag(
                "EXAM_DRUG_MISMATCH",
                "FAIL",
                "Exam and drug mismatch",
                "Selected radiopharmaceutical is not allowed for this exam.",
                "Choose an allowed radiopharmaceutical.",
                tags=["dose"],
            )
        )

    suggested_dose = None
    if isinstance(draft_payload, dict):
        suggested = draft_payload.get("suggestedDose")
        if isinstance(suggested, dict):
            value = suggested.get("value")
            if isinstance(value, (int, float)):
                suggested_dose = value

    min_dose = dose_policy.get("min") if isinstance(dose_policy, dict) else None
    max_dose = dose_policy.get("max") if isinstance(dose_policy, dict) else None
    if suggested_dose is not None and isinstance(min_dose, (int, float)) and isinstance(max_dose, (int, float)):
        if suggested_dose < min_dose or suggested_dose > max_dose:
            flags.append(
                _flag(
                    "DOSE_OUT_OF_RANGE",
                    "FAIL",
                    "Dose out of range",
                    "Suggested dose is outside the configured range.",
                    "Adjust dose to the allowed range.",
                    tags=["dose"],
                )
            )

    override = False
    if isinstance(draft_payload, dict):
        override_payload = draft_payload.get("override")
        if isinstance(override_payload, dict):
            override = bool(override_payload.get("isOverride"))
    if override:
        flags.append(
            _flag(
                "OVERRIDE_REQUIRES_REVIEW",
                "WARN",
                "Override requires review",
                "Override requested by NM.",
                "Review override justification before approval.",
                tags=["dose"],
            )
        )

    overall = "PASS"
    for flag in flags:
        severity = flag.get("severity", "PASS")
        if _severity_rank(severity) > _severity_rank(overall):
            overall = severity
    overallSeverity = "FAIL" if overall == "FAIL" else "WARN" if overall == "WARN" else "PASS"

    has_fail = any(flag.get("severity") == "FAIL" for flag in flags)
    required_present = True
    if "WEIGHT_KG" in required_facts and not has_weight_local:
        required_present = False
    if "RENAL_FUNCTION" in required_facts and not has_renal_local:
        required_present = False

    is_batch_eligible = (
        overallSeverity != "FAIL"
        and not has_fail
        and required_present
        and not override
    )

    return {
        "overallSeverity": overallSeverity,
        "isBatchEligible": bool(is_batch_eligible),
        "flags": flags,
    }
