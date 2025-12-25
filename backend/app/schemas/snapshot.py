"""
Patient Snapshot 與 Auto-fill 相關 Schema
依據 spec/99_full_spec_reference.md Addendum B 定義
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union
from pydantic import BaseModel


class FactType(str, Enum):
    """臨床事實類型"""
    WEIGHT_KG = "WEIGHT_KG"
    EGFR = "EGFR"
    SCR_MGDL = "SCR_MGDL"
    ALLERGY_SUMMARY = "ALLERGY_SUMMARY"


class SourceType(str, Enum):
    """資料來源類型"""
    FHIR_RESOURCE = "FHIR_RESOURCE"
    DOCUMENT_TEXT = "DOCUMENT_TEXT"
    NOTE_TEXT = "NOTE_TEXT"
    MANUAL = "MANUAL"
    AUTOFILL = "AUTOFILL"


class Confidence(str, Enum):
    """信心度等級"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ExtractionMethod(str, Enum):
    """擷取方法"""
    STRUCTURED = "STRUCTURED"
    PATTERN = "PATTERN"
    NLP = "NLP"


class CandidateFact(BaseModel):
    """自動填入候選值
    
    Attributes:
        factType: 事實類型
        value: 數值或文字
        unit: 單位 (UCUM)
        asOf: 來源時間
        sourceType: 資料來源類型
        sourceRef: 來源參考 (FHIR reference 或 document id)
        sourceSnippet: 來源摘要片段（用於 UI 顯示）
        confidence: 信心度
        extractionMethod: 擷取方法
        derived: 衍生資訊
    """
    factType: FactType
    value: Union[float, str]
    unit: Optional[str] = None
    asOf: datetime
    sourceType: SourceType
    sourceRef: Optional[str] = None
    sourceSnippet: Optional[str] = None
    confidence: Confidence
    extractionMethod: ExtractionMethod
    derived: Optional[dict[str, Any]] = None


class SnapshotData(BaseModel):
    """病人快照資料"""
    conditions: list[dict[str, Any]] = []
    allergies: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []


class PatientSnapshotResponse(BaseModel):
    """病人快照回應"""
    caseId: str
    patientRef: str
    serviceRequestRef: str
    snapshot: SnapshotData
    candidateFacts: list[CandidateFact]


class AcceptAutoFillFact(BaseModel):
    """接受的自動填入事實"""
    factType: FactType
    value: Union[float, str]
    unit: Optional[str] = None
    asOf: datetime
    sourceType: SourceType
    sourceRef: Optional[str] = None
    confidence: Confidence
    extractionMethod: ExtractionMethod


class AcceptAutoFillRequest(BaseModel):
    """接受自動填入請求"""
    caseId: str
    facts: list[AcceptAutoFillFact]
    acceptedBy: Optional[str] = None  # 由 token 覆蓋
    reason: Optional[str] = None


class AcceptAutoFillResponse(BaseModel):
    """接受自動填入回應"""
    caseId: str
    updatedLocalFacts: dict[str, Any]
    cds: dict[str, Any]  # RuleEval 格式


class RejectAutoFillItem(BaseModel):
    """拒絕的自動填入項目"""
    factType: FactType
    sourceRef: Optional[str] = None
    reason: Optional[str] = None


class RejectAutoFillRequest(BaseModel):
    """拒絕自動填入請求"""
    caseId: str
    rejections: list[RejectAutoFillItem]


class RejectAutoFillResponse(BaseModel):
    """拒絕自動填入回應"""
    caseId: str
    rejected: bool = True

