# Analytics & KPI (Research-ready)


## Implementation Targets
- Language: Python 3.11+
- Framework: FastAPI
- Database: SQLite (demo-first), via SQLAlchemy 2.x (async optional)
- FHIR Server (external): HAPI FHIR R4 (baseUrl=http://localhost:8080/fhir)
- Mode: Production Mode + Demo Mode (APP_MODE=production|demo)
- Realtime updates: SSE preferred (WebSocket optional)
- Auth: Demo Mode uses local mock login; Production Mode uses OIDC token validation (stub allowed)
- Principle: Low-coupling HIS integration (read minimal facts; defer write-back of final MedicationRequest)


## MUST Metrics
- Missing data rate (before/after autofill/manual completion)
- Auto-fill candidate generation/accept/reject counts and rates
- Pharmacist intervention rate (RETURN + REJECT) / total submitted
- Return reason distribution (codes)
- Physician response action distribution
- TAT:
  - NM draft -> submit
  - submit -> first pharmacist action
  - submit -> approve/return
- Batch approval rate

## MUST Endpoints
- /api/analytics/summary
- /api/analytics/autofill/summary

## SHOULD Output Format
- Provide both aggregate and breakdown arrays to support pivot tables.
