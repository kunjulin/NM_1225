# Nonfunctional Requirements (Demo-first)


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
- Timeouts on outbound FHIR calls (e.g., 2-5s) + graceful fallback to snapshot cache
- Idempotency for webhook/seed operations
- Input validation and clear error codes
- Protect demo endpoints behind APP_MODE=demo

## SHOULD
- Basic structured logging (caseId, actor, action)
- SQLite WAL mode for concurrency (demo)
- Rate limit webhook endpoint (simple)

## OPTIONAL
- OIDC token validation (production stub)
