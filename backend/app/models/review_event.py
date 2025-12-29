"""
ReviewEvent 資料模型
審查事件記錄表，儲存所有操作的稽核軌跡
"""
from typing import Optional

from sqlalchemy import String, Text, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReviewEvent(Base):
    """ReviewEvent 資料表
    
    記錄所有案件操作事件，用於稽核與分析
    依據 spec/02_data_model.md 定義
    
    事件類型 (event_type):
    - CLAIM: 藥師 Claim 案件
    - SUBMIT: 核醫送審
    - RETURN: 藥師退回
    - APPROVE: 藥師核准
    - REJECT: 藥師拒絕
    - RESPONSE: 核醫回應退回
    - AUTOFILL_ACCEPT: 接受自動填入
    - AUTOFILL_REJECT: 拒絕自動填入
    - SYNC_SUCCESS: 同步成功
    - SYNC_FAIL: 同步失敗
    """
    __tablename__ = "review_events"
    
    # 主鍵
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # 關聯案件
    case_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("order_cases.id"),
        index=True
    )
    
    # 事件類型
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    
    # 執行者資訊
    actor_subject: Mapped[str] = mapped_column(String(100))
    acting_role: Mapped[str] = mapped_column(String(50))
    
    # 事件載荷（結構化 JSON）
    payload_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 時間戳記
    created_at: Mapped[str] = mapped_column(String(50))
    
    # 複合索引
    __table_args__ = (
        Index("ix_review_events_case_created", "case_id", "created_at"),
    )






