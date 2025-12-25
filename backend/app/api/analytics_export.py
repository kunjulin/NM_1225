from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.analytics_export import (
    export_all_zip,
    export_autofill_csv,
    export_returns_csv,
    export_summary_csv,
    export_tat_csv,
)


router = APIRouter(prefix="/analytics/export", tags=["analytics"])


def _filename(prefix: str, from_date: str, to_date: str, ext: str) -> str:
    return f"{prefix}_{from_date.replace('-', '')}_{to_date.replace('-', '')}.{ext}"


@router.get("/summary.csv")
def export_summary_route(
    from_date: str = Query(..., alias="from", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    to_date: str = Query(..., alias="to", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
):
    csv_bytes = export_summary_csv(db, from_date, to_date)
    filename = _filename("analytics_summary", from_date, to_date, "csv")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/returns.csv")
def export_returns_route(
    from_date: str = Query(..., alias="from", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    to_date: str = Query(..., alias="to", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
):
    csv_bytes = export_returns_csv(db, from_date, to_date)
    filename = _filename("analytics_returns", from_date, to_date, "csv")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/tat.csv")
def export_tat_route(
    from_date: str = Query(..., alias="from", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    to_date: str = Query(..., alias="to", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
):
    csv_bytes = export_tat_csv(db, from_date, to_date)
    filename = _filename("analytics_tat", from_date, to_date, "csv")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/autofill.csv")
def export_autofill_route(
    from_date: str = Query(..., alias="from", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    to_date: str = Query(..., alias="to", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
):
    csv_bytes = export_autofill_csv(db, from_date, to_date)
    filename = _filename("analytics_autofill", from_date, to_date, "csv")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/all.zip")
def export_all_route(
    from_date: str = Query(..., alias="from", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    to_date: str = Query(..., alias="to", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
):
    zip_bytes = export_all_zip(db, from_date, to_date)
    filename = _filename("analytics_export", from_date, to_date, "zip")
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
