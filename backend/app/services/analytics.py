from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import OrderCase, Outbox, ReviewEvent


def _parse_json(payload: str) -> dict[str, Any]:
    if not payload:
        return {}
    try:
        parsed = json.loads(payload)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _parse_dt(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _range_bounds(from_str: str, to_str: str) -> tuple[str, str]:
    start = datetime.combine(date.fromisoformat(from_str), time.min, tzinfo=timezone.utc)
    end = datetime.combine(date.fromisoformat(to_str), time.min, tzinfo=timezone.utc) + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    values_sorted = sorted(values)
    index = int((percentile / 100) * len(values_sorted)) - 1
    index = max(0, min(index, len(values_sorted) - 1))
    return float(values_sorted[index])


def _tat_stats(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "p50Seconds": None, "p90Seconds": None, "meanSeconds": None}
    return {
        "count": len(values),
        "p50Seconds": _percentile(values, 50),
        "p90Seconds": _percentile(values, 90),
        "meanSeconds": sum(values) / len(values),
    }


def _extract_rule_flags(case: OrderCase) -> list[dict]:
    payload = _parse_json(case.draft_json)
    rule_eval = payload.get("ruleEval") if isinstance(payload, dict) else None
    flags = rule_eval.get("flags") if isinstance(rule_eval, dict) else None
    return flags if isinstance(flags, list) else []


def summary(db: Session, from_str: str, to_str: str) -> dict:
    start, end = _range_bounds(from_str, to_str)

    total_cases = (
        db.query(OrderCase)
        .filter(OrderCase.created_at >= start, OrderCase.created_at < end)
        .count()
    )

    events = (
        db.query(ReviewEvent)
        .filter(ReviewEvent.created_at >= start, ReviewEvent.created_at < end)
        .all()
    )
    outbox_rows = (
        db.query(Outbox)
        .filter(Outbox.updated_at >= start, Outbox.updated_at < end)
        .all()
    )

    event_counts = Counter(event.event_type for event in events)
    submitted = event_counts.get("SUBMIT", 0)
    returns = event_counts.get("RETURN", 0)
    approvals = event_counts.get("APPROVE", 0)

    sync_done = sum(1 for row in outbox_rows if row.status == "DONE")
    sync_failed = sum(1 for row in outbox_rows if row.status == "FAILED")

    return_reason_counts: Counter[str] = Counter()
    response_action_counts: Counter[str] = Counter()
    return_case_ids: set[str] = set()
    for event in events:
        payload = _parse_json(event.payload_json)
        if event.event_type == "RETURN":
            return_case_ids.add(event.case_id)
            for code in payload.get("returnReasonCodes", []) or []:
                return_reason_counts[str(code)] += 1
        if event.event_type == "RESPONSE":
            action = payload.get("responseAction")
            if action:
                response_action_counts[str(action)] += 1

    # Best-effort dose proxy using current ruleEval and return reasons.
    submit_case_ids = {event.case_id for event in events if event.event_type == "SUBMIT"}
    cases = (
        db.query(OrderCase)
        .filter(OrderCase.id.in_(submit_case_ids))
        .all()
        if submit_case_ids
        else []
    )
    inappropriate_cases: set[str] = set()
    for case in cases:
        flags = _extract_rule_flags(case)
        if any(flag.get("code") == "DOSE_OUT_OF_RANGE" for flag in flags):
            inappropriate_cases.add(case.id)
        draft = _parse_json(case.draft_json)
        override = draft.get("override") if isinstance(draft, dict) else None
        if isinstance(override, dict) and override.get("isOverride") is True:
            inappropriate_cases.add(case.id)
    for event in events:
        if event.event_type == "RETURN":
            payload = _parse_json(event.payload_json)
            if "DOSE_OUT_OF_RANGE" in (payload.get("returnReasonCodes") or []):
                inappropriate_cases.add(event.case_id)

    inappropriate_rate = (
        len(inappropriate_cases) / submitted if submitted else 0.0
    )

    # Best-effort missing data flags using latest stored ruleEval.
    missing_weight_cases = 0
    missing_renal_cases = 0
    for case in cases:
        flags = _extract_rule_flags(case)
        if any(flag.get("code") == "MISSING_WEIGHT" for flag in flags):
            missing_weight_cases += 1
        if any(flag.get("code") == "MISSING_RENAL_FUNCTION" for flag in flags):
            missing_renal_cases += 1

    # TAT metrics.
    events_by_case: dict[str, list[ReviewEvent]] = defaultdict(list)
    for event in db.query(ReviewEvent).filter(ReviewEvent.case_id.in_(submit_case_ids)).all():
        events_by_case[event.case_id].append(event)

    tat_first_pharm: list[float] = []
    tat_decision: list[float] = []
    for case_id, case_events in events_by_case.items():
        submit_times = [e for e in case_events if e.event_type == "SUBMIT"]
        if not submit_times:
            continue
        submit_time = min(
            (e for e in submit_times if _parse_dt(e.created_at)),
            key=lambda e: _parse_dt(e.created_at),
        )
        submit_dt = _parse_dt(submit_time.created_at)
        if not submit_dt:
            continue
        pharm_actions = [
            e for e in case_events if e.event_type in {"CLAIM", "RETURN", "APPROVE"}
        ]
        decision_actions = [
            e for e in case_events if e.event_type in {"RETURN", "APPROVE"}
        ]
        if pharm_actions:
            next_pharm = min(
                (e for e in pharm_actions if _parse_dt(e.created_at)),
                key=lambda e: _parse_dt(e.created_at),
            )
            pharm_dt = _parse_dt(next_pharm.created_at)
            if pharm_dt and pharm_dt >= submit_dt:
                tat_first_pharm.append((pharm_dt - submit_dt).total_seconds())
        if decision_actions:
            next_decision = min(
                (e for e in decision_actions if _parse_dt(e.created_at)),
                key=lambda e: _parse_dt(e.created_at),
            )
            decision_dt = _parse_dt(next_decision.created_at)
            if decision_dt and decision_dt >= submit_dt:
                tat_decision.append((decision_dt - submit_dt).total_seconds())

    tat_approve_sync: list[float] = []
    approve_events = [e for e in events if e.event_type == "APPROVE"]
    outbox_by_case = defaultdict(list)
    for row in db.query(Outbox).all():
        outbox_by_case[row.case_id].append(row)
    for event in approve_events:
        approve_dt = _parse_dt(event.created_at)
        if not approve_dt:
            continue
        rows = [r for r in outbox_by_case.get(event.case_id, []) if r.status == "DONE"]
        if not rows:
            continue
        row = min(
            (r for r in rows if _parse_dt(r.updated_at)),
            key=lambda r: _parse_dt(r.updated_at),
        )
        done_dt = _parse_dt(row.updated_at)
        if done_dt and done_dt >= approve_dt:
            tat_approve_sync.append((done_dt - approve_dt).total_seconds())

    intervention_rate = returns / submitted if submitted else 0.0

    return {
        "range": {"from": from_str, "to": to_str},
        "counts": {
            "totalCasesCreated": total_cases,
            "submittedToPharmacy": submitted,
            "pharmacistInterventions": returns,
            "approvals": approvals,
            "syncDone": sync_done,
            "syncFailed": sync_failed,
        },
        "kpis": {
            "pharmacistInterventionRate": intervention_rate,
            "inappropriateDoseCases": len(inappropriate_cases),
            "inappropriateDoseRate": inappropriate_rate,
            "missingData": {
                "missingWeightCases": missing_weight_cases,
                "missingRenalCases": missing_renal_cases,
            },
        },
        "tat": {
            "submitToFirstPharmAction": _tat_stats(tat_first_pharm),
            "submitToDecision": _tat_stats(tat_decision),
            "approveToSyncDone": _tat_stats(tat_approve_sync),
        },
        "distributions": {
            "returnReasons": [
                {"code": code, "count": count}
                for code, count in return_reason_counts.items()
            ],
            "responseActions": [
                {"code": code, "count": count}
                for code, count in response_action_counts.items()
            ],
        },
        "breakdowns": {},
    }


def autofill_summary(db: Session, from_str: str, to_str: str) -> dict:
    start, end = _range_bounds(from_str, to_str)

    events = (
        db.query(ReviewEvent)
        .filter(ReviewEvent.created_at >= start, ReviewEvent.created_at < end)
        .all()
    )

    accepted_events = [e for e in events if e.event_type == "AUTOFILL_ACCEPT"]
    rejected_events = [e for e in events if e.event_type == "AUTOFILL_REJECT"]

    by_fact: dict[str, dict[str, int]] = defaultdict(lambda: {"accepted": 0, "rejected": 0})
    accepted_case_ids: set[str] = set()

    for event in accepted_events:
        accepted_case_ids.add(event.case_id)
        payload = _parse_json(event.payload_json)
        for fact in payload.get("facts", []) or []:
            fact_type = str(fact.get("factType"))
            if fact_type:
                by_fact[fact_type]["accepted"] += 1

    for event in rejected_events:
        payload = _parse_json(event.payload_json)
        for rejection in payload.get("rejections", []) or []:
            fact_type = str(rejection.get("factType"))
            if fact_type:
                by_fact[fact_type]["rejected"] += 1

    # Best-effort impact using current ruleEval.
    missing_weight_resolved = 0
    missing_renal_resolved = 0
    if accepted_case_ids:
        cases = db.query(OrderCase).filter(OrderCase.id.in_(accepted_case_ids)).all()
        for case in cases:
            flags = _extract_rule_flags(case)
            if not any(flag.get("code") == "MISSING_WEIGHT" for flag in flags):
                missing_weight_resolved += 1
            if not any(flag.get("code") == "MISSING_RENAL_FUNCTION" for flag in flags):
                missing_renal_resolved += 1

    accepted_count = len(accepted_events)
    rejected_count = len(rejected_events)
    total = accepted_count + rejected_count
    accept_rate = accepted_count / total if total else 0.0

    return {
        "range": {"from": from_str, "to": to_str},
        "autofill": {
            "candidatesGenerated": 0,
            "acceptedEvents": accepted_count,
            "rejectedEvents": rejected_count,
            "acceptRate": accept_rate,
            "byFactType": [
                {"factType": fact_type, **counts} for fact_type, counts in by_fact.items()
            ],
            "impact": {
                "missingWeightResolved": missing_weight_resolved,
                "missingRenalResolved": missing_renal_resolved,
            },
        },
    }
