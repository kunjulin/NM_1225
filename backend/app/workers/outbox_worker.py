from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import OrderCase, Outbox
from app.db.session import SessionLocal
from app.fhir.mappers import map_medication_request
from app.fhir.validator import validate_medication_request
from app.integrations.fhir_client import create_medication_request


MAX_RETRY = 3


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


def _claim_next(db: Session) -> Outbox | None:
    row = (
        db.query(Outbox)
        .filter(Outbox.status == "PENDING")
        .order_by(Outbox.created_at)
        .first()
    )
    if not row:
        return None

    updated = (
        db.query(Outbox)
        .filter(Outbox.id == row.id, Outbox.status == "PENDING")
        .update({"status": "IN_PROGRESS", "updated_at": _now_iso()})
    )
    if updated == 0:
        db.rollback()
        return None
    db.commit()
    return db.query(Outbox).filter(Outbox.id == row.id).one_or_none()


def _mark_success(db: Session, row: Outbox, result_ref: str) -> None:
    payload = _parse_json(row.request_json)
    payload["resultRef"] = result_ref
    row.request_json = json.dumps(payload)
    row.status = "DONE"
    row.last_error = None
    row.updated_at = _now_iso()
    db.add(row)

    case = db.query(OrderCase).filter(OrderCase.id == row.case_id).one_or_none()
    if case:
        case.status = "SYNCED"
        case.updated_at = _now_iso()
        db.add(case)

    db.commit()


def _mark_failure(db: Session, row: Outbox, error: str) -> None:
    row.retry_count += 1
    row.last_error = error
    row.updated_at = _now_iso()
    if row.retry_count >= MAX_RETRY:
        row.status = "FAILED"
        case = db.query(OrderCase).filter(OrderCase.id == row.case_id).one_or_none()
        if case:
            case.status = "SYNC_FAILED"
            case.updated_at = _now_iso()
            db.add(case)
    else:
        row.status = "PENDING"
    db.add(row)
    db.commit()


def process_once(db: Session) -> bool:
    row = _claim_next(db)
    if not row:
        return False

    try:
        request_payload = _parse_json(row.request_json)
        case = db.query(OrderCase).filter(OrderCase.id == row.case_id).one_or_none()
        if not case:
            _mark_failure(db, row, "OrderCase not found.")
            return True
        fhir_payload = map_medication_request(case)
        fhir_payload.update(request_payload.get("overrides", {}))
        validation_errors = validate_medication_request(fhir_payload)
        if validation_errors:
            _mark_failure(db, row, "VALIDATION_ERROR: " + "; ".join(validation_errors))
            return True
        result_ref = create_medication_request(fhir_payload)
        _mark_success(db, row, result_ref)
        return True
    except Exception as exc:  # noqa: BLE001
        _mark_failure(db, row, str(exc))
        return True


def run_worker(poll_interval: float = 2.0) -> None:
    while True:
        db = SessionLocal()
        try:
            processed = process_once(db)
        finally:
            db.close()
        if not processed:
            break
        time.sleep(poll_interval)


if __name__ == "__main__":
    run_worker()
