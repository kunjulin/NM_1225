from __future__ import annotations

from pydantic import BaseModel


class Range(BaseModel):
    from_date: str
    to_date: str


class TatStats(BaseModel):
    count: int
    p50Seconds: float | None
    p90Seconds: float | None
    meanSeconds: float | None


class SummaryResponse(BaseModel):
    range: dict
    counts: dict
    kpis: dict
    tat: dict
    distributions: dict
    breakdowns: dict


class AutofillSummaryResponse(BaseModel):
    range: dict
    autofill: dict
