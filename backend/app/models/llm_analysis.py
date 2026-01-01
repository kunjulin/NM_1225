"""
LLMAnalysis 資料模型
儲存 LLM 分析結果
"""
from typing import Optional

from sqlalchemy import String, Text, Integer, Float, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LLMAnalysis(Base):
    """LLMAnalysis 資料表
    
    儲存 LLM 臨床分析結果
    每次分析都會建立一筆新記錄，可追溯歷史
    """
    __tablename__ = "llm_analyses"
    
    # 主鍵
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # 關聯的案件 ID
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("order_cases.id"), index=True)
    
    # 分析狀態: PENDING, PROCESSING, COMPLETED, FAILED
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    
    # 使用的模型名稱
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 使用的 prompt（完整組合後的）
    prompt_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # LLM 原始回應
    raw_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 解析後的 JSON 結果（結構化）
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 錯誤訊息（如果失敗）
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 執行時間（毫秒）
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Token 使用量
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 觸發者
    triggered_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 觸發方式: MANUAL, AUTO
    trigger_type: Mapped[str] = mapped_column(String(20), default="MANUAL")
    
    # 時間戳記
    created_at: Mapped[str] = mapped_column(String(50))
    updated_at: Mapped[str] = mapped_column(String(50))
    
    # 複合索引：按案件和時間排序
    __table_args__ = (
        Index("ix_llm_analyses_case_created", "case_id", "created_at"),
    )


class AnalysisStatus:
    """分析狀態常數"""
    PENDING = "PENDING"         # 等待處理
    PROCESSING = "PROCESSING"   # 處理中
    COMPLETED = "COMPLETED"     # 完成
    FAILED = "FAILED"           # 失敗


class TriggerType:
    """觸發類型常數"""
    MANUAL = "MANUAL"   # 手動觸發
    AUTO = "AUTO"       # 自動觸發

