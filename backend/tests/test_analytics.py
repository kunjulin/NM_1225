from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.db.session import get_db
from app.main import app


def _setup_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _date_range():
    today = datetime.now(timezone.utc).date().isoformat()
    return today, today


def test_analytics_summary_shape() -> None:
    client = _setup_client()
    from_date, to_date = _date_range()
    seed = client.post("/api/demo/seed")
    assert seed.status_code == 200
    response = client.get(f"/api/analytics/summary?from={from_date}&to={to_date}")
    assert response.status_code == 200
    payload = response.json()
    assert "counts" in payload
    assert "kpis" in payload
    assert "tat" in payload
    assert "distributions" in payload
    assert "breakdowns" in payload


def test_analytics_autofill_summary_shape() -> None:
    client = _setup_client()
    from_date, to_date = _date_range()
    seed = client.post("/api/demo/seed")
    assert seed.status_code == 200
    response = client.get(f"/api/analytics/autofill/summary?from={from_date}&to={to_date}")
    assert response.status_code == 200
    payload = response.json()
    assert "autofill" in payload
    assert "acceptRate" in payload["autofill"]
