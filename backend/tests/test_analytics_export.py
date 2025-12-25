from __future__ import annotations

import zipfile
from datetime import datetime, timezone
from io import BytesIO

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


def test_export_summary_csv() -> None:
    client = _setup_client()
    from_date, to_date = _date_range()
    seed = client.post("/api/demo/seed")
    assert seed.status_code == 200
    response = client.get(f"/api/analytics/export/summary.csv?from={from_date}&to={to_date}")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    text = response.text
    assert "totalCasesCreated" in text.splitlines()[0]


def test_export_all_zip_contains_files() -> None:
    client = _setup_client()
    from_date, to_date = _date_range()
    seed = client.post("/api/demo/seed")
    assert seed.status_code == 200
    response = client.get(f"/api/analytics/export/all.zip?from={from_date}&to={to_date}")
    assert response.status_code == 200
    assert "application/zip" in response.headers.get("content-type", "")
    with zipfile.ZipFile(BytesIO(response.content), "r") as archive:
        names = set(archive.namelist())
    assert {"summary.csv", "returns.csv", "tat.csv", "autofill.csv", "metadata.json"}.issubset(names)
