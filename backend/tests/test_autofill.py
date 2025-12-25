from __future__ import annotations

import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, OrderCase, ReviewEvent
from app.schemas.snapshot import CandidateFact
from app.services.autofill import accept_autofill, reject_autofill
from app.services.snapshot import get_snapshot


def _make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()


def _seed_case(db, snapshot: dict, draft: dict | None = None, local_facts: dict | None = None) -> OrderCase:
    case = OrderCase(
        id="case-1",
        patient_ref="Patient/1",
        service_request_ref="ServiceRequest/1",
        status="NM_DRAFTED",
        owner_subject=None,
        snapshot_json=json.dumps(snapshot),
        local_facts_json=json.dumps(local_facts or {}),
        draft_json=json.dumps(
            draft
            or {
                "examCode": "BONE_SCAN",
                "radiopharmaceuticalCode": "LOCAL_BONE_01",
                "suggestedDose": {"value": 200, "unit": "MBq"},
                "override": {"isOverride": False, "reason": ""},
            }
        ),
        final_fhir_medication_request_ref=None,
        created_at="2025-01-01T00:00:00+00:00",
        updated_at="2025-01-02T00:00:00+00:00",
    )
    db.add(case)
    db.commit()
    return case


def test_snapshot_returns_weight_candidate() -> None:
    db = _make_session()
    _seed_case(
        db,
        snapshot={
            "weights": [
                {
                    "value": 70,
                    "unit": "kg",
                    "asOf": "2025-01-01T00:00:00+00:00",
                    "sourceRef": "Observation/1",
                }
            ]
        },
    )
    result = get_snapshot(db, "case-1", refresh=False)
    candidates = result["candidateFacts"]
    assert any(
        fact.factType == "WEIGHT_KG" and fact.value == 70 for fact in candidates
    )


def test_accept_weight_updates_local_facts_and_rules() -> None:
    db = _make_session()
    _seed_case(db, snapshot={})
    fact = CandidateFact(
        factType="WEIGHT_KG",
        value=70,
        unit="kg",
        asOf="2025-01-02T00:00:00+00:00",
        sourceType="LOCAL_SNAPSHOT",
        sourceRef="snapshot_json",
        sourceSnippet=None,
        confidence="HIGH",
        extractionMethod="STRUCTURED",
    )
    result = accept_autofill(
        db,
        "case-1",
        [fact],
        reason=None,
        actor_subject="demo-user",
        acting_role="NM_PHYSICIAN",
    )
    updated = result["updatedLocalFacts"]
    assert updated["weightKg"]["source"] == "AUTOFILL"
    codes = {flag["code"] for flag in result["cds"]["flags"]}
    assert "MISSING_WEIGHT" not in codes
    assert "LOCAL_DATA_USED" in codes


def test_reject_creates_review_event() -> None:
    db = _make_session()
    _seed_case(db, snapshot={})
    reject_autofill(
        db,
        "case-1",
        [{"factType": "WEIGHT_KG", "sourceRef": "Observation/1", "reason": "stale"}],
        actor_subject="demo-user",
        acting_role="NM_PHYSICIAN",
    )
    event = (
        db.query(ReviewEvent)
        .filter(ReviewEvent.case_id == "case-1", ReviewEvent.event_type == "AUTOFILL_REJECT")
        .one_or_none()
    )
    assert event is not None
