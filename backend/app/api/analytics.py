"""
Analytics API 路由
KPI 與統計分析
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import AnalyticsSummary, AutofillSummary
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import get_current_user, CurrentUser

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    from_date: date = Query(..., alias="from", description="起始日期"),
    to_date: date = Query(..., alias="to", description="結束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得 KPI 摘要
    
    包含：
    - 不適當劑量比例
    - 藥師介入率
    - 處理時間統計
    - 退回原因分佈
    """
    service = AnalyticsService(db)
    return await service.get_summary(from_date, to_date)


@router.get("/autofill/summary", response_model=AutofillSummary)
async def get_autofill_summary(
    from_date: date = Query(..., alias="from", description="起始日期"),
    to_date: date = Query(..., alias="to", description="結束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得 Auto-fill 統計摘要"""
    service = AnalyticsService(db)
    return await service.get_autofill_summary(from_date, to_date)

