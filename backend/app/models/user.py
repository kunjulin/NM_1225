"""
User 資料模型
使用者與角色管理

Production Mode 下，使用者透過 SMART on FHIR 登入後會自動建立，
需由管理員審核並指派角色後才能使用系統。
"""
from enum import Enum
from typing import Optional

from sqlalchemy import String, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserStatus(str, Enum):
    """使用者狀態"""
    PENDING = "PENDING"      # 待審核（新使用者首次登入）
    ACTIVE = "ACTIVE"        # 已啟用
    INACTIVE = "INACTIVE"    # 已停用


class User(Base):
    """User 資料表
    
    儲存系統使用者資訊與角色權限
    支援 SMART on FHIR 登入取得的 Practitioner 身份
    """
    __tablename__ = "users"
    
    # 主鍵
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # 使用者識別碼（SMART sub 或員工編號）- UNIQUE
    subject: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    
    # FHIR Practitioner 參考（如 "Practitioner/123"）
    practitioner_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 顯示名稱（從 Practitioner 資源取得或手動設定）
    display_name: Mapped[str] = mapped_column(String(200))
    
    # 電子郵件（可選）
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # 允許的角色（JSON 陣列，如 '["NM_PHYSICIAN", "PHARMACIST"]'）
    allowed_roles: Mapped[str] = mapped_column(Text, default='[]')
    
    # 使用者狀態
    status: Mapped[str] = mapped_column(String(20), default=UserStatus.PENDING.value, index=True)
    
    # 是否為管理員（用於首次建立預設管理員）
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 最後登入時間
    last_login_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 時間戳記
    created_at: Mapped[str] = mapped_column(String(50))
    updated_at: Mapped[str] = mapped_column(String(50))
    
    # 複合索引
    __table_args__ = (
        Index("ix_users_status_updated", "status", "updated_at"),
    )


