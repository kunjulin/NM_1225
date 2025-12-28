"""
規則引擎輸出 Schema
依據 spec/04_rules_engine.md 定義
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Severity(str, Enum):
    """嚴重度等級"""
    INFO = "INFO"
    WARN = "WARN"
    FAIL = "FAIL"
    PASS = "PASS"


class RuleFlag(BaseModel):
    """規則旗標
    
    Attributes:
        code: 旗標代碼 (e.g., MISSING_WEIGHT, DOSE_OUT_OF_RANGE)
        severity: 嚴重度等級
        title: 顯示標題
        explain: 詳細說明
        recommendation: 建議處理方式
        dataRefs: 相關 FHIR 資源參考
        tags: 標籤 (用於分類，如 dose, renal, allergy, demo)
    """
    code: str
    severity: Severity
    title: str
    explain: str
    recommendation: Optional[str] = None
    dataRefs: list[str] = []
    tags: list[str] = []


class RuleEval(BaseModel):
    """規則引擎評估結果
    
    Attributes:
        overallSeverity: 整體嚴重度 (PASS, WARN, FAIL)
        isBatchEligible: 是否符合批次核准資格
        flags: 所有觸發的規則旗標
    """
    overallSeverity: Severity
    isBatchEligible: bool
    flags: list[RuleFlag] = []
    
    @classmethod
    def passing(cls) -> "RuleEval":
        """建立一個通過的評估結果"""
        return cls(
            overallSeverity=Severity.PASS,
            isBatchEligible=True,
            flags=[]
        )




