# NM SMART on FHIR Medication Stewardship — Codex-Ready Specification (SQLite Demo)


## Implementation Targets
- Language: Python 3.11+
- Framework: FastAPI
- Database: SQLite (demo-first), via SQLAlchemy 2.x (async optional)
- FHIR Server (external): HAPI FHIR R4 (baseUrl=http://localhost:8080/fhir)
- Mode: Production Mode + Demo Mode (APP_MODE=production|demo)
- Realtime updates: SSE preferred (WebSocket optional)
- Auth: Demo Mode uses local mock login; Production Mode uses OIDC token validation (stub allowed)
- Principle: Low-coupling HIS integration (read minimal facts; defer write-back of final MedicationRequest)


## Scope Summary
This spec defines a SMART on FHIR–enabled nuclear medicine radiopharmaceutical medication stewardship system with:
- Local workflow (OrderCase/ReviewTask) and audit trail
- Minimal HIS/THAS FHIR usage: read ServiceRequest/Patient/Observation; write final MedicationRequest only
- NM and Pharmacy worklists, claim/owner mechanism, return-response loop
- Rule engine output structure (flags, severity, explain) to drive UI grouping
- Demo Mode for single-partition THAS environment (role view switch + scenario seeding)
- Auto-fill from patient snapshot with candidate facts + accept/reject
- Analytics endpoints for KPI and research

## Non-goals (Do not implement)
- Do not store PHI beyond what is required for demo; minimize snapshot retention.
- Do not write intermediate workflow states (claim/return) back to HIS FHIR.
- Do not depend on THAS multi-tenant/partition features.
- Do not implement full production-grade SMART launch flow for demo (stub is acceptable).
- Do not implement NLP extraction beyond simple pattern-based parsing unless explicitly requested.

## Source Document
The full narrative spec is preserved in: SMART_on_FHIR_Medication_Stewardship_Spec_TWCore_Final.md
