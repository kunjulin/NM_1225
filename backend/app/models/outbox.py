"""
Outbox 資料模型
延遲寫回佇列表，用於非同步同步 MedicationRequest 到 FHIR Server
"""
from typing import Optional

from sqlalchemy import String, Text, Integer, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Outbox(Base):
    """Outbox 資料表
    
    實作 Outbox Pattern 進行延遲 write-back
    依據 spec/02_data_model.md 定義
    
    操作類型 (operation):
    - CREATE_MEDICATION_REQUEST: 建立 MedicationRequest
    
    狀態 (status):
    - PENDING: 待處理
    - IN_PROGRESS: 處理中
    - DONE: 已完成
    - FAILED: 失敗
    """
    __tablename__ = "outbox"
    
    # 主鍵
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # 關聯案件
    case_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("order_cases.id"),
        index=True
    )
    
    # 操作類型
    operation: Mapped[str] = mapped_column(String(50))
    
    # 請求載荷
    request_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 處理狀態
    status: Mapped[str] = mapped_column(String(20), index=True)
    
    # 錯誤資訊
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 重試資訊
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    next_retry_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 時間戳記
    created_at: Mapped[str] = mapped_column(String(50))
    updated_at: Mapped[str] = mapped_column(String(50))
    
    # 複合索引
    __table_args__ = (
        Index("ix_outbox_status_retry", "status", "next_retry_at"),
    )


