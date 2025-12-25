# Acceptance Tests (Given/When/Then)


## Implementation Targets
- Language: Python 3.11+
- Framework: FastAPI
- Database: SQLite (demo-first), via SQLAlchemy 2.x (async optional)
- FHIR Server (external): HAPI FHIR R4 (baseUrl=http://localhost:8080/fhir)
- Mode: Production Mode + Demo Mode (APP_MODE=production|demo)
- Realtime updates: SSE preferred (WebSocket optional)
- Auth: Demo Mode uses local mock login; Production Mode uses OIDC token validation (stub allowed)
- Principle: Low-coupling HIS integration (read minimal facts; defer write-back of final MedicationRequest)


## Scenario 1 — Missing weight -> manual completion -> CDS rerun
Given a case with no weight from HIS and localFacts.weightKg is null
When NM opens case detail
Then ruleEval.flags includes MISSING_WEIGHT
When NM submits local weight via POST /nm/cases/{caseId}/draft or a dedicated completion endpoint
Then localFacts.weightKg is set and ruleEval no longer includes MISSING_WEIGHT (or severity reduced)

## Scenario 2 — Snapshot autofill -> accept -> CDS rerun
Given a case with missing weight
When GET /cases/{caseId}/snapshot
Then candidateFacts includes WEIGHT_KG with confidence != LOW
When POST /cases/{caseId}/autofill/accept with that fact
Then localFacts.weightKg.source == AUTOFILL and CDS is recalculated

## Scenario 3 — Pharmacy return -> NM respond -> resubmit
Given a submitted case in PHARM_READY
When pharmacist returns with reason MISSING_DATA
Then case status becomes RETURNED and review_events contains RETURN
When NM responds with ADDED_MISSING_DATA and updates draft
Then review_events contains RESPONSE and status becomes NM_DRAFTED
When NM submits again
Then status becomes PHARM_READY

## Scenario 4 — Batch approve only eligible cases
Given multiple PHARM_READY cases where some have FAIL flags
When POST /pharmacy/bulk-approve with all caseIds
Then eligible cases become APPROVED and ineligible cases return failed[] with code NOT_BATCH_ELIGIBLE or HAS_FAIL_FLAGS

## Scenario 5 — Approved triggers deferred write-back
Given a case approved by pharmacist
When outbox worker runs
Then MedicationRequest is created in FHIR and case status becomes SYNCED; on failure becomes SYNC_FAILED with retry metadata
