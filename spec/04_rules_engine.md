# Rule Engine Contract — Output First


## Implementation Targets
- Language: Python 3.11+
- Framework: FastAPI
- Database: SQLite (demo-first), via SQLAlchemy 2.x (async optional)
- FHIR Server (external): HAPI FHIR R4 (baseUrl=http://localhost:8080/fhir)
- Mode: Production Mode + Demo Mode (APP_MODE=production|demo)
- Realtime updates: SSE preferred (WebSocket optional)
- Auth: Demo Mode uses local mock login; Production Mode uses OIDC token validation (stub allowed)
- Principle: Low-coupling HIS integration (read minimal facts; defer write-back of final MedicationRequest)


## MUST: RuleEval Output Schema
Rule engine returns:
{
  "overallSeverity": "PASS|WARN|FAIL",
  "isBatchEligible": true,
  "flags": [
    {
      "code": "MISSING_WEIGHT",
      "severity": "INFO|WARN|FAIL",
      "title": "string",
      "explain": "string",
      "recommendation": "string",
      "dataRefs": ["Observation/123"],
      "tags": ["dose","renal","allergy","demo"]
    }
  ]
}

## MUST: Flags required by spec
- MISSING_WEIGHT (FAIL or WARN per policy)
- MISSING_RENAL_FUNCTION
- ALLERGY_REVIEW_REQUIRED
- LOCAL_DATA_USED (INFO)
- DOSE_OUT_OF_RANGE
- OVERRIDE_REQUIRES_REVIEW
- EXAM_DRUG_MISMATCH

## MUST: Batch Eligibility Rules
- isBatchEligible can be true only if:
  - overallSeverity != FAIL
  - no flags with severity FAIL
  - required facts present (weight/renal per exam)
  - pharmacist policy allows batch approval

## SHOULD: Config-driven rules
- rules_config.yaml mapping:
  - examCode -> radiopharmaceutical
  - pediatric dose parameters (NA-2024 mapping)
  - min/max dose
  - required facts
  - override policy

## OPTIONAL: Parsing snapshot documents
- In demo, PATTERN extraction is sufficient.
