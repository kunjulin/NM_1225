"""
測試資料 API 路由
用於生成測試資料（Production Mode 也可使用）
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.demo import SeedRequest, SeedResponse
from app.services.demo_service import DemoService
from app.services.auth_service import get_current_user, CurrentUser

router = APIRouter()


@router.post("/seed", response_model=SeedResponse)
async def seed_test_data(
    request: SeedRequest = SeedRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """建立測試資料
    
    包含：
    - 成人標準劑量案例
    - 兒童體重調整案例
    - 腎功能不全案例
    - 缺乏體重資料案例（autofill 測試）
    - 劑量超出範圍案例
    - 已批准案例（用於 CSV 匯出測試）
    """
    service = DemoService(db)
    return await service.seed_test_data(request, current_user)


@router.post("/reset")
async def reset_test_data(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """重置測試資料（清除所有本地資料）"""
    service = DemoService(db)
    await service.reset_all()
    return {"message": "Test data reset successfully"}

