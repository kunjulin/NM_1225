"""
OrderCase 資料模型
案件主表，儲存工作流程狀態與臨床資料快照
"""
from typing import Optional

from sqlalchemy import String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OrderCase(Base):
    """OrderCase 資料表
    
    儲存核子醫學用藥案件的完整狀態
    依據 spec/02_data_model.md 定義
    """
    __tablename__ = "order_cases"
    
    # 主鍵
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # FHIR 資源參考
    patient_ref: Mapped[str] = mapped_column(String(100), index=True)
    service_request_ref: Mapped[str] = mapped_column(String(100), index=True)
    
    # 工作流程狀態
    status: Mapped[str] = mapped_column(String(50), index=True)
    
    # 當前擁有者（藥師 Claim 後設定）
    owner_subject: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # JSON 資料欄位
    snapshot_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    local_facts_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    draft_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 最終同步的 FHIR 資源參考
    final_fhir_medication_request_ref: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    
    # 時間戳記
    created_at: Mapped[str] = mapped_column(String(50))
    updated_at: Mapped[str] = mapped_column(String(50))
    
    # 複合索引
    __table_args__ = (
        Index("ix_order_cases_status_updated", "status", "updated_at"),
        Index("ix_order_cases_patient_updated", "patient_ref", "updated_at"),
    )


