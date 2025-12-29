"""
Demo Mode 相關 Schema
依據 spec/05_demo_mode_thas.md 定義
"""
from typing import Optional
from pydantic import BaseModel

from app.schemas.case import ActingRole


class SetActingRoleRequest(BaseModel):
    """設定操作角色請求"""
    actingRole: ActingRole


class WhoAmIResponse(BaseModel):
    """當前身份回應"""
    subject: str
    actingRole: ActingRole
    appMode: str
    isDemo: bool


class SeedScenario(BaseModel):
    """示範情境"""
    name: str
    description: str
    cases: int


class SeedRequest(BaseModel):
    """建立示範資料請求"""
    scenarios: Optional[list[str]] = None  # 若為空則建立所有情境
    clearExisting: bool = False


class SeedResponse(BaseModel):
    """建立示範資料回應"""
    created: int
    scenarios: list[SeedScenario]





