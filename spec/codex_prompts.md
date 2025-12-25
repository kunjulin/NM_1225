# Codex Prompt Templates

## General instruction (paste before each task)
You are implementing a demo-first system strictly following the provided spec. Do not invent new fields or endpoints.
If anything is ambiguous, add TODO comments in code rather than making assumptions.
Use SQLite and keep the implementation minimal but correct.

## Task 1: Scaffold
Create a monorepo with FastAPI backend and SQLite (SQLAlchemy). Provide docker-compose to run backend and HAPI FHIR R4 (optional).

## Task 2: Data model + migrations
Implement tables: order_cases, review_events, outbox as defined in 02_data_model.md.

## Task 3: Core APIs
Implement endpoints in 03_api_contract.md, with Pydantic models matching the schemas.

## Task 4: Rule engine
Implement rule engine output schema in 04_rules_engine.md with config-driven rules_config.yaml.

## Task 5: Auto-fill snapshot
Implement snapshot retrieval and candidateFacts generation + accept/reject per 03_api_contract.md and 04_rules_engine.md.

## Task 6: Analytics
Implement /analytics/summary and /analytics/autofill/summary per 06_analytics_kpi.md.

## Task 7: Tests
Implement pytest scenarios in 08_acceptance_tests.md.
