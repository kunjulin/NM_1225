Overview

This document defines frontend implementation tasks (F0–F5) for the Nuclear Medicine Medication Stewardship SMART-on-FHIR Demo.

Backend APIs are already implemented.

This frontend MUST strictly follow backend contracts and
spec/99_full_spec_reference.md as the single source of truth.

Each task is designed to be executed independently using Cursor Agent Mode with GPT-5.2-codex.

Global Frontend Constraints (APPLY TO ALL TASKS)

Tech stack (DO NOT CHANGE):

React 18 + TypeScript

Vite

React Router

@tanstack/react-query

MUI (Material UI)

Fetch-based API client

Auth / Session:

Demo-first

Header-based auth only:

X-Subject

X-Acting-Role

No OIDC implementation (stub allowed only)

API Base URL:

http://localhost:8000/api


Rules:

No business logic duplication in frontend

No backend data mocking

UI reflects backend payloads exactly

Role-based rendering only (no permission logic reimplementation)

F0 — Frontend Scaffold
Objective

Create a clean React + Vite frontend scaffold with routing and providers.

Spec References

spec/99_full_spec_reference.md (frontend scope only)

Prompt (paste into Cursor Agent)
You are implementing Frontend Step F0: Project Scaffold.

Context:
- Frontend for SMART-on-FHIR–style medication stewardship system.
- Backend APIs already exist.

Tech stack (DO NOT CHANGE):
- React 18 + TypeScript
- Vite
- React Router
- @tanstack/react-query
- MUI

Tasks:
1. Create frontend project under /frontend using Vite + React + TS.
2. Folder structure:
   - src/
     - app/
     - pages/
     - components/
     - api/
     - hooks/
     - types/
   - src/main.tsx
   - src/App.tsx
3. Configure React Router with placeholder routes:
   - /login
   - /nm/worklist
   - /pharmacy/worklist
   - /case/:caseId
   - /analytics
4. Configure React Query provider.
5. Implement basic App Shell (layout + outlet).
6. Add README section: how to run frontend.

Constraints:
- No UI logic.
- No backend calls yet.
- No mock data.

Deliverables:
- Frontend project scaffold
- App loads with empty routes

Acceptance

npm run dev starts

Empty pages render without error

F1 — Demo Login + Role Switch
Objective

Enable demo login and acting-role switching compatible with single-partition FHIR demo.

Spec References

spec/99_full_spec_reference.md (Demo Mode, role switching)

Backend demo endpoints

Prompt
You are implementing Frontend Step F1: Demo Login + Role Switch.

Backend APIs:
- POST /api/demo/set-acting-role
- GET /api/demo/whoami

Tasks:
1. Implement /login page:
   - Input: subject
   - ActingRole selector: NM_PHYSICIAN | PHARMACIST | ADMIN
2. Create AuthContext:
   - Stores subject, actingRole, appMode
   - Injects X-Subject & X-Acting-Role headers globally
3. App Shell Top Bar:
   - Display subject
   - Display actingRole
   - DEMO MODE badge
   - Role switcher (demo only)
4. Route guard:
   - Redirect to /login if not logged in
   - Block NM routes for PHARMACIST and vice versa

Constraints:
- Demo only
- No OIDC
- Explicit logic (no magic)

Deliverables:
- Working login + role switch
- Backend reflects actingRole changes

F2 — NM Worklist Page
Objective

Display Nuclear Medicine physician worklist with CDS indicators.

Spec References

spec/99_full_spec_reference.md (NM worklist)

Backend:

GET /api/nm/worklist

Prompt
You are implementing Frontend Step F2: NM Worklist.

Tasks:
1. NM Worklist page with filters/tabs:
   - NM_PENDING
   - NM_DRAFTED
   - RETURNED
   - PHARM_READY (read-only)
2. Fetch via React Query.
3. Render grouped list:
   - group title
   - count
   - rows
4. Each row shows:
   - patient
   - exam
   - status
   - severity badge (ruleEval.overallSeverity)
   - flags count
   - updated time
5. Click row → /case/:caseId

Constraints:
- No rule logic in frontend
- Render backend payload as-is

Deliverables:
- Functional NM Worklist

F3 — Pharmacy Worklist Page (Batch Support)
Objective

Enable pharmacist review with batch approval.

Spec References

spec/99_full_spec_reference.md (Pharmacy worklist grouping)

Prompt
You are implementing Frontend Step F3: Pharmacy Worklist.

Backend:
- GET /api/pharmacy/worklist
- POST /api/pharmacy/bulk-approve

Tasks:
1. Three sections:
   - Pass Queue (batch eligible)
   - Exceptions
   - My Claimed
2. Each row shows:
   - patient
   - exam
   - flags
   - severity
3. Actions:
   - Claim
   - Approve
   - Return
4. Batch approve:
   - Only Pass Queue
   - Checkbox select
   - Call bulk-approve
   - Show per-item result summary

Constraints:
- UI action enablement based only on backend state
- No duplicate validation

Deliverables:
- Pharmacy worklist
- Batch approve working

F4 — Case Detail Page (NM + Pharmacy)
Objective

Unified case view for NM and Pharmacy with CDS, snapshot, autofill, audit.

Spec References

spec/99_full_spec_reference.md (Case detail, autofill, audit)

Prompt
You are implementing Frontend Step F4: Case Detail Page.

Backend APIs:
- snapshot
- autofill accept/reject
- draft/submit/approve/return/respond

Tasks:
1. Layout sections:
   - Order & indication
   - Patient snapshot
   - CDS / RuleEval panel
2. Auto-fill:
   - Show candidateFacts
   - Multi-select accept
   - Reject
3. NM actions:
   - Edit draft
   - Submit
   - Respond to return
4. Pharmacy actions:
   - Claim
   - Approve
   - Return with reason codes
5. Audit timeline (review_events)

Constraints:
- Role-based rendering only
- No backend rule recreation

Deliverables:
- Full Case Detail workflow

F5 — Analytics Dashboard
Objective

Visualize KPIs and enable CSV/ZIP export.

Spec References

spec/99_full_spec_reference.md (Analytics & research KPIs)

Prompt
You are implementing Frontend Step F5: Analytics Dashboard.

Backend:
- GET /api/analytics/summary
- GET /api/analytics/autofill/summary
- CSV/ZIP export endpoints

Tasks:
1. Date range selector
2. KPI cards:
   - Pharmacist intervention rate
   - Inappropriate dose rate
   - Autofill accept rate
3. Charts:
   - Return reason distribution
   - TAT (p50/p90)
4. Export buttons:
   - summary.csv
   - all.zip
5. Handle loading/empty/error states

Constraints:
- Simple charts OK
- No data processing beyond display

Deliverables:
- Analytics dashboard usable for demo & screenshots

Recommended Execution Order
F0 → F1 → F2 → F3 → F4 → F5


Do NOT skip steps.