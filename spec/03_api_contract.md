# API Contract (FastAPI) — MUST Endpoints


## Implementation Targets
- Language: Python 3.11+
- Framework: FastAPI
- Database: SQLite (demo-first), via SQLAlchemy 2.x (async optional)
- FHIR Server (external): HAPI FHIR R4 (baseUrl=http://localhost:8080/fhir)
- Mode: Production Mode + Demo Mode (APP_MODE=production|demo)
- Realtime updates: SSE preferred (WebSocket optional)
- Auth: Demo Mode uses local mock login; Production Mode uses OIDC token validation (stub allowed)
- Principle: Low-coupling HIS integration (read minimal facts; defer write-back of final MedicationRequest)


## Conventions
- Base URL: /api
- All responses JSON
- ErrorResponse:
{
  "error": {
    "code": "STRING",
    "message": "STRING",
    "details": { }
  }
}

## MUST: Worklists

### GET /nm/worklist?status=NM_PENDING|RETURNED|NM_DRAFTED
Response 200:
{
  "groups": [
    {"groupKey":"NM_PENDING","title":"待核醫處理","count":0,"items":[...]},
    {"groupKey":"RETURNED","title":"藥師退回待回應","count":0,"items":[...]}
  ]
}

### GET /pharmacy/worklist?status=PHARM_READY|PHARM_IN_PROGRESS
Response 200 MUST be grouped for UI:
{
  "groups": [
    {"groupKey":"exceptions","title":"需逐筆審查","count":0,"items":[WorklistItem]},
    {"groupKey":"batchEligible","title":"可批次核准","count":0,"items":[WorklistItem]},
    {"groupKey":"myClaimed","title":"我已Claim","count":0,"items":[WorklistItem]}
  ]
}

WorklistItem MUST include:
- caseId, patientRef, serviceRequestRef, status, ownerSubject(optional)
- snapshotSummary (small)
- ruleEval: {overallSeverity,isBatchEligible,flags[]}

## MUST: NM Draft + Submit

### POST /nm/cases/{caseId}/draft
Request:
{ "draft": {...} }
Response 200: updated WorklistItem + ruleEval

### POST /nm/cases/{caseId}/submit
Behavior MUST:
- Change status to PHARM_READY
- Create review event SUBMIT
Response 200: { "caseId":"...", "status":"PHARM_READY" }

## MUST: Pharmacy Claim / Approve / Return

### POST /pharmacy/cases/{caseId}/claim
MUST:
- If status != PHARM_READY => 409 INVALID_STATE
- Else set status=PHARM_IN_PROGRESS and owner_subject=login subject atomically
Response 200: { "caseId":"...", "status":"PHARM_IN_PROGRESS", "ownerSubject":"..." }

### POST /pharmacy/bulk-approve
Request:
{ "caseIds": ["..."], "note": "optional" }
MUST:
- For each caseId: auto-claim if needed then approve if batchEligible AND no FAIL flags
- Return per-case outcomes
Response 200:
{ "ok":[{"caseId":"...","status":"APPROVED"}], "failed":[{"caseId":"...","code":"...","message":"..."}] }

### POST /pharmacy/cases/{caseId}/approve
MUST:
- Only owner can approve when in progress (or auto-claim then approve)
- Set status=APPROVED and enqueue outbox write-back
Response 200: { "caseId":"...", "status":"APPROVED" }

### POST /pharmacy/cases/{caseId}/return
Request:
{
  "returnReasonCodes": ["DOSE_OUT_OF_RANGE","MISSING_DATA","MISMATCH","ALLERGY_CONCERN"],
  "comment": "string"
}
MUST:
- Set status=RETURNED; clear owner_subject
- Create review event RETURN with structured reasons
Response 200: { "caseId":"...", "status":"RETURNED" }

## MUST: Return Response

### POST /nm/cases/{caseId}/respond
Request:
{
  "responseAction": "UPDATED_DOSE|ADDED_MISSING_DATA|PROVIDED_OVERRIDE_JUSTIFICATION|CANCELLED_ORDER",
  "comment": "string"
}
MUST:
- Create draft revision; create review event RESPONSE
Response 200: { "caseId":"...", "status":"NM_DRAFTED" }

## MUST: Patient Snapshot + Auto-fill

### GET /cases/{caseId}/snapshot?refresh=false
Returns snapshot + candidateFacts[]

### POST /cases/{caseId}/autofill/accept
Accept one or more candidate facts; persist into local_facts_json (source=AUTOFILL); rerun CDS.

### POST /cases/{caseId}/autofill/reject
Persist rejections for audit and reduce repeated prompts.

## MUST: Analytics

### GET /analytics/summary?from=YYYY-MM-DD&to=YYYY-MM-DD
Return KPI summary including:
- inappropriate dose rate (proxy via FAIL flags / overrides)
- pharmacist intervention rate (RETURN/REJECT)
- TAT stats
- return reasons distribution
- response action distribution
- missing data rate + autofill accept rate

### GET /analytics/autofill/summary?from=YYYY-MM-DD&to=YYYY-MM-DD
Auto-fill metrics + impact fields.

## SHOULD: Demo Mode endpoints

### POST /demo/seed
Create demo cases and optional FHIR seed resources.

### POST /demo/set-acting-role
Change actingRole for UI; audit retains login subject.
