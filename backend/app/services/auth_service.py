"""
認證與授權服務
Demo Mode: 使用 Header-based auth (X-Subject, X-Acting-Role)
Production Mode: 驗證使用者角色是否在 User 表中被允許
"""
import json
from typing import Optional
from dataclasses import dataclass

from fastapi import Header, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.case import ActingRole
from app.config import get_settings
from app.database import get_db


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
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """從 Header 取得當前使用者
    
    Demo Mode:
    - X-Subject: 使用者識別碼 (必填)
    - X-Acting-Role: 操作角色 (NM_PHYSICIAN, PHARMACIST, ADMIN)
    - 若未提供，使用預設值
    
    Production Mode:
    - 必須提供 X-Subject 和 X-Acting-Role
    - 驗證使用者存在於 User 表中
    - 驗證使用者狀態為 ACTIVE
    - 驗證使用者被允許使用該角色
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
        # Production Mode: 必須提供有效的認證並驗證角色
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
        
        # 驗證使用者是否存在且有權限
        from app.models.user import User, UserStatus
        
        result = await db.execute(
            select(User).where(User.subject == x_subject)
        )
        user = result.scalar_one_or_none()
        
        # 特殊處理：預設管理員帳號 (admin) 允許直接登入（用於首次設定）
        if not user and x_subject == "admin":
            # 檢查是否有預設管理員，如果沒有則建立
            admin_result = await db.execute(
                select(User).where(User.subject == "admin")
            )
            admin_user = admin_result.scalar_one_or_none()
            
            if not admin_user:
                # 建立預設管理員（如果不存在）
                import uuid
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc).isoformat()
                admin_user = User(
                    id=str(uuid.uuid4()),
                    subject="admin",
                    practitioner_ref=None,
                    display_name="系統管理員",
                    email=None,
                    allowed_roles='["ADMIN"]',
                    status=UserStatus.ACTIVE.value,
                    is_admin=True,
                    last_login_at=now,
                    created_at=now,
                    updated_at=now,
                )
                db.add(admin_user)
                await db.commit()
            
            user = admin_user
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found. Please login via SMART on FHIR first."
            )
        
        if user.status == UserStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is pending approval by administrator"
            )
        
        if user.status == UserStatus.INACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # 驗證角色權限
        allowed_roles = json.loads(user.allowed_roles or "[]")
        
        # ADMIN 可以使用任何角色
        if "ADMIN" not in allowed_roles and x_acting_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have permission to use role: {x_acting_role}"
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


