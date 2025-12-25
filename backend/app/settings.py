from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    app_mode: str
    database_url: str
    fhir_base_url: str | None


def get_settings() -> Settings:
    app_mode = os.getenv("APP_MODE", "demo")
    backend_dir = Path(__file__).resolve().parents[1]
    default_db_path = backend_dir / "backend.db"
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = f"sqlite:///{default_db_path.as_posix()}"
    fhir_base_url = os.getenv("FHIR_BASE_URL")
    return Settings(
        app_mode=app_mode,
        database_url=database_url,
        fhir_base_url=fhir_base_url,
    )
