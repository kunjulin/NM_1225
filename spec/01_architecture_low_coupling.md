# Architecture — Low Coupling and Deferred Synchronization


## Implementation Targets
- Language: Python 3.11+
- Framework: FastAPI
- Database: SQLite (demo-first), via SQLAlchemy 2.x (async optional)
- FHIR Server (external): HAPI FHIR R4 (baseUrl=http://localhost:8080/fhir)
- Mode: Production Mode + Demo Mode (APP_MODE=production|demo)
- Realtime updates: SSE preferred (WebSocket optional)
- Auth: Demo Mode uses local mock login; Production Mode uses OIDC token validation (stub allowed)
- Principle: Low-coupling HIS integration (read minimal facts; defer write-back of final MedicationRequest)


## MUST
- Maintain local workflow state in SQLite (OrderCase/ReviewTask + review_events).
- Read from HIS/THAS FHIR only the minimal clinical facts needed for CDS:
  - ServiceRequest (exam order)
  - Patient (identifier + display)
  - Observation (weight, renal function)
  - OPTIONAL: AllergyIntolerance/Condition only if rules require
- Final write-back: create MedicationRequest in HIS/THAS only when workflow reaches APPROVED (Pharmacy approved).

## SHOULD
- Use snapshot caching: when a case is created/refreshed, store a minimal snapshot_json in local DB.
- Use outbox table for deferred write-back (so FHIR slowness does not block UI).

## OPTIONAL
- FHIR Subscription rest-hook to notify new ServiceRequest; otherwise implement polling by _lastUpdated.

## System Components
- FastAPI backend (business logic + rules + analytics)
- Local SQLite database (workflow + audit + metrics)
- Frontend SMART app (minimal pages) OR API-only demo (Postman)
- External HAPI FHIR server for facts ingestion and final MedicationRequest write-back

## State Machine (OrderCase.status)
- NM_PENDING: created from ServiceRequest; awaiting NM review
- NM_DRAFTED: NM draft exists (local)
- PHARM_READY: submitted to pharmacy review
- PHARM_IN_PROGRESS: claimed by pharmacist (owner set)
- RETURNED: returned to NM with reasons
- APPROVED: pharmacist approved; triggers write-back
- SYNCING: write-back in progress (outbox pending)
- SYNCED: MedicationRequest created in FHIR (final)
- SYNC_FAILED: write-back failed (retry)

## Concurrency / Ownership
- Claim MUST be atomic at backend level:
  - Only one pharmacist can claim a case/task at a time.
  - Enforce via DB transaction and status check.
