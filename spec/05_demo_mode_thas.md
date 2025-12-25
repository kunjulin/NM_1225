# Demo Mode (FHIR 50 / THAS) — Single Partition Friendly


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
- APP_MODE=demo enables:
  - UI Role View Switch: NM_PHYSICIAN / PHARMACIST
  - Demo Scenario Seeding
  - Clear UI label: DEMO MODE
- Audit MUST record:
  - login subject
  - actingRole (view switch)
  - actions + timestamps

## SHOULD
- Provide a deterministic seed set:
  - adult standard case
  - pediatric weight-adjusted case
  - renal impairment case
  - missing weight case (autofill suggested)
  - dose out-of-range case (forces return)

## OPTIONAL
- Seed minimal FHIR resources to THAS:
  - ServiceRequest, Observation
- Avoid depending on THAS auth; demo auth can be local.
