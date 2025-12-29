"""
Demo Mode API 路由
僅在 APP_MODE=demo 時啟用
"""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    SetActingRoleRequest,
    WhoAmIResponse,
    ActingRole,
)
from app.schemas.demo import SeedRequest, SeedResponse
from app.services.demo_service import DemoService
from app.services.auth_service import get_current_user, CurrentUser
from app.config import get_settings

router = APIRouter()


@router.get("/whoami", response_model=WhoAmIResponse)
async def whoami(
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得當前登入者身份資訊"""
    settings = get_settings()
    return WhoAmIResponse(
        subject=current_user.subject,
        actingRole=current_user.acting_role,
        appMode=settings.app_mode.value,
        isDemo=settings.is_demo_mode,
    )


@router.post("/set-acting-role", response_model=WhoAmIResponse)
async def set_acting_role(
    request: SetActingRoleRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """切換操作角色（Demo Mode 專用）
    
    允許在單一 partition 環境下模擬多角色操作
    """
    settings = get_settings()
    # 在實際實作中，這會更新 session 或返回新的 token
    # Demo 模式下，角色由 X-Acting-Role header 控制
    return WhoAmIResponse(
        subject=current_user.subject,
        actingRole=request.actingRole,
        appMode=settings.app_mode.value,
        isDemo=settings.is_demo_mode,
    )


@router.post("/seed", response_model=SeedResponse)
async def seed_demo_data(
    request: SeedRequest = SeedRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """建立示範資料
    
    包含：
    - 成人標準劑量案例
    - 兒童體重調整案例
    - 腎功能不全案例
    - 缺乏體重資料案例（autofill 測試）
    - 劑量超出範圍案例
    """
    service = DemoService(db)
    return await service.seed_demo_data(request, current_user)


@router.post("/reset")
async def reset_demo_data(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """重置示範資料（清除所有本地資料）"""
    service = DemoService(db)
    await service.reset_all()
    return {"message": "Demo data reset successfully"}





