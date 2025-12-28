"""
Analytics 相關 Schema
依據 spec/06_analytics_kpi.md 定義
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel


class DateWindow(BaseModel):
    """日期區間"""
    from_date: date
    to_date: date


class TATStats(BaseModel):
    """處理時間統計"""
    median: float
    p50: float
    p90: float
    mean: float


class ReturnReasonStat(BaseModel):
    """退回原因統計"""
    code: str
    count: int
    rate: float


class ResponseActionStat(BaseModel):
    """回應動作統計"""
    action: str
    count: int
    rate: float


class AnalyticsSummary(BaseModel):
    """分析摘要回應
    
    包含主要與次要評估指標
    """
    window: DateWindow
    
    # 主要指標
    totalCases: int
    inappropriateDoseRate: float  # 不適當劑量比例
    pharmacistInterventionRate: float  # 藥師介入率
    
    # 次要指標
    medianTAT: float  # 中位數處理時間 (分鐘)
    batchApprovalRate: float  # 批次核准比例
    
    # 分佈資料
    returnReasons: list[ReturnReasonStat]
    responseActions: list[ResponseActionStat]
    
    # 缺失資料統計
    missingDataRate: float
    overrideRate: float
    
    # TAT 詳細統計
    tatStats: Optional[TATStats] = None


class FactTypeStat(BaseModel):
    """按事實類型的統計"""
    factType: str
    generated: int
    accepted: int
    rejected: int
    acceptRate: float


class AutofillImpact(BaseModel):
    """Auto-fill 影響分析"""
    missingDataRateBefore: float
    missingDataRateAfter: float
    medianTATBefore: float
    medianTATAfter: float


class AutofillSummary(BaseModel):
    """Auto-fill 統計摘要"""
    window: DateWindow
    candidatesGenerated: int
    candidatesAccepted: int
    candidatesRejected: int
    acceptRate: float
    byFactType: list[FactTypeStat]
    impact: Optional[AutofillImpact] = None




