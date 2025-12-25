"""
認證與授權服務
Demo Mode: 使用 Header-based auth (X-Subject, X-Acting-Role)
Production Mode: 使用 OIDC token validation (stub)
"""
from typing import Optional
from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from app.schemas.case import ActingRole
from app.config import get_settings


@dataclass
class CurrentUser:
    """當前使用者資訊"""
    subject: str
    acting_role: ActingRole
    
    @property
    def is_nm_physician(self) -> bool:
        return self.acting_role == ActingRole.NM_PHYSICIAN
    
    @property
    def is_pharmacist(self) -> bool:
        return self.acting_role == ActingRole.PHARMACIST
    
    @property
    def is_admin(self) -> bool:
        return self.acting_role == ActingRole.ADMIN


async def get_current_user(
    x_subject: Optional[str] = Header(None, alias="X-Subject"),
    x_acting_role: Optional[str] = Header(None, alias="X-Acting-Role"),
) -> CurrentUser:
    """從 Header 取得當前使用者
    
    Demo Mode:
    - X-Subject: 使用者識別碼 (必填)
    - X-Acting-Role: 操作角色 (NM_PHYSICIAN, PHARMACIST, ADMIN)
    
    若未提供，使用預設值 (Demo Mode)
    """
    settings = get_settings()
    
    if settings.is_demo_mode:
        # Demo Mode: 允許未認證存取，使用預設值
        subject = x_subject or "demo-user"
        role_str = x_acting_role or "NM_PHYSICIAN"
        
        try:
            acting_role = ActingRole(role_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid acting role: {role_str}. Must be one of: {[r.value for r in ActingRole]}"
            )
        
        return CurrentUser(subject=subject, acting_role=acting_role)
    
    else:
        # Production Mode: 必須提供有效的認證
        if not x_subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-Subject header"
            )
        
        if not x_acting_role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-Acting-Role header"
            )
        
        try:
            acting_role = ActingRole(x_acting_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid acting role: {x_acting_role}"
            )
        
        return CurrentUser(subject=x_subject, acting_role=acting_role)


def require_role(*roles: ActingRole):
    """角色檢查裝飾器"""
    async def dependency(current_user: CurrentUser = Header(...)):
        if current_user.acting_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {[r.value for r in roles]}"
            )
        return current_user
    return dependency

