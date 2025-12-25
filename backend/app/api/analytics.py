from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import AutofillSummaryResponse, SummaryResponse
from app.services.analytics import autofill_summary, summary


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=SummaryResponse)
def analytics_summary_route(
    from_date: str = Query(..., alias="from", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    to_date: str = Query(..., alias="to", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
):
    return summary(db, from_date, to_date)


@router.get("/autofill/summary", response_model=AutofillSummaryResponse)
def analytics_autofill_route(
    from_date: str = Query(..., alias="from", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    to_date: str = Query(..., alias="to", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
):
    return autofill_summary(db, from_date, to_date)
