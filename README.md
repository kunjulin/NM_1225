# NM Medication Stewardship (Backend)

## Local run

1. Create a virtual environment and install dependencies (PowerShell):

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

2. Start the API server:

```powershell
python -m uvicorn app.main:app --reload
```

3. Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Configuration

- `APP_MODE`: `demo` (default) or `production`
- `DATABASE_URL`: SQLAlchemy URL; defaults to a local SQLite file at `backend/backend.db`
- `FHIR_BASE_URL`: FHIR base URL for write-back (omit in demo to use stub)
- Python: 3.13 (or 3.11+)

## Demo mode

Run the API in demo mode (default):

```powershell
$env:APP_MODE="demo"
python -m uvicorn app.main:app --reload
```

Seed deterministic demo cases:

```bash
curl -X POST http://127.0.0.1:8000/api/demo/seed
```

Switch acting role (stored in memory per subject):

```bash
curl -X POST http://127.0.0.1:8000/api/demo/set-acting-role ^
  -H "Content-Type: application/json" ^
  -H "X-Subject: demo-user" ^
  -d "{\"actingRole\":\"PHARMACIST\"}"
```

Check current demo identity:

```bash
curl http://127.0.0.1:8000/api/demo/whoami -H "X-Subject: demo-user"
```

## Outbox worker

Approving a case creates an outbox row. Run the worker to process deferred write-back:

```bash
python -m app.workers.outbox_worker
```

Demo mode (or no `FHIR_BASE_URL`) logs the payload and returns a fake `MedicationRequest/*` id.

Inspect outbox rows in demo mode:

```bash
curl http://127.0.0.1:8000/api/admin/outbox
```

## TW Core mapping & validation

Mapping catalog lives at `backend/app/mapping/catalog.yaml`. Add local codes by extending:

```yaml
radiopharmaceuticals:
  LOCAL_NEW_01:
    display: "New Radiopharm"
    system: "http://example.org/local/radiopharm"
    doseUnitDefault: "MBq"
procedures:
  NEW_EXAM:
    display: "New Exam"
    system: "http://example.org/local/procedure"
```

Approval now validates required fields before enqueueing outbox. Typical errors:
- missing `patientRef` or `serviceRequestRef`
- unknown `radiopharmaceuticalCode` (not in catalog)
- missing `suggestedDose.value` or `suggestedDose.unit`

Worker validates the generated MedicationRequest before posting and marks the outbox row `FAILED` on validation errors.

## Analytics export

Export KPI summary:

```bash
curl -OJ "http://127.0.0.1:8000/api/analytics/export/summary.csv?from=2025-01-01&to=2025-01-31"
```

Export all analytics files as ZIP:

```bash
curl -OJ "http://127.0.0.1:8000/api/analytics/export/all.zip?from=2025-01-01&to=2025-01-31"
```
