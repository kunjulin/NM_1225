# Data Model (SQLite) — Single Source of Truth


## Implementation Targets
- Language: Python 3.11+
- Framework: FastAPI
- Database: SQLite (demo-first), via SQLAlchemy 2.x (async optional)
- FHIR Server (external): HAPI FHIR R4 (baseUrl=http://localhost:8080/fhir)
- Mode: Production Mode + Demo Mode (APP_MODE=production|demo)
- Realtime updates: SSE preferred (WebSocket optional)
- Auth: Demo Mode uses local mock login; Production Mode uses OIDC token validation (stub allowed)
- Principle: Low-coupling HIS integration (read minimal facts; defer write-back of final MedicationRequest)


## MUST Tables

### table: order_cases
- id TEXT (uuid, pk)
- patient_ref TEXT (indexed)          # e.g., 'Patient/123'
- service_request_ref TEXT (indexed)  # e.g., 'ServiceRequest/456'
- status TEXT (indexed)               # enum values in architecture doc
- owner_subject TEXT NULL             # current claimed owner (pharmacist) when in progress
- snapshot_json TEXT                  # JSON string (minimal facts + course summary)
- local_facts_json TEXT               # JSON string (manual completion + accepted autofill)
- draft_json TEXT                     # JSON string (NM medication draft payload)
- final_fhir_medication_request_ref TEXT NULL
- created_at TEXT (ISO datetime)
- updated_at TEXT (ISO datetime)

### table: review_events
- id TEXT (uuid, pk)
- case_id TEXT (fk -> order_cases.id, indexed)
- event_type TEXT (indexed)           # e.g., CLAIM, SUBMIT, RETURN, APPROVE, REJECT, AUTOFILL_ACCEPT, AUTOFILL_REJECT, SYNC_SUCCESS, SYNC_FAIL
- actor_subject TEXT                  # login subject
- acting_role TEXT                    # NM_PHYSICIAN / PHARMACIST / ADMIN
- payload_json TEXT                   # structured payload (reasons, responseAction, flags, etc.)
- created_at TEXT

### table: outbox
- id TEXT (uuid, pk)
- case_id TEXT (fk, indexed)
- operation TEXT                      # CREATE_MEDICATION_REQUEST
- request_json TEXT                   # payload to post to FHIR
- status TEXT                         # PENDING, IN_PROGRESS, DONE, FAILED
- last_error TEXT NULL
- retry_count INTEGER
- next_retry_at TEXT NULL
- created_at TEXT
- updated_at TEXT

## JSON Structures (stored in *_json fields)

### local_facts_json
{
  "weightKg": {"value": 70.5, "asOf": "2025-12-25T00:00:00+08:00", "source": "HIS|MANUAL|AUTOFILL", "sourceRef": "Observation/123", "enteredBy": "A12345"},
  "renal": {"eGFR": {"value": 65, "unit": "mL/min/1.73m2", "asOf": "...", "source": "..."}},
  "allergySummary": {"value": "NKDA", "asOf": "...", "source": "..."},
  "notes": "optional"
}

### draft_json (NM medication draft)
{
  "examCode": "BONE_SCAN|MAG3|DMSA|MIBG|FDG_PET",
  "radiopharmaceuticalCode": "localCode",
  "suggestedDose": {"value": 185, "unit": "MBq"},
  "override": {"isOverride": false, "reason": ""},
  "ruleEval": { ... see rule engine output ... }
}

### snapshot_json (minimal patient snapshot)
- Store minimal elements only:
  - recent weights / renal labs summary
  - allergy summary
  - problem list summary (Condition)
  - links to underlying FHIR refs (do not duplicate full resources)

## SHOULD Indexes
- order_cases(status, updated_at)
- order_cases(patient_ref, updated_at)
- review_events(case_id, created_at)
- outbox(status, next_retry_at)
