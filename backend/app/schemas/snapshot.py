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


class EncounterInfo(BaseModel):
    """就醫紀錄資訊"""
    id: str
    status: Optional[str] = None
    classCode: Optional[str] = None  # 就醫類別: AMB(門診), EMER(急診), IMP(住院)
    classDisplay: Optional[str] = None
    typeCode: Optional[str] = None
    typeDisplay: Optional[str] = None
    periodStart: Optional[str] = None
    periodEnd: Optional[str] = None
    reasonCode: Optional[str] = None
    reasonDisplay: Optional[str] = None
    location: Optional[str] = None


class ConditionInfo(BaseModel):
    """診斷/病史資訊"""
    id: str
    clinicalStatus: Optional[str] = None  # active, recurrence, relapse, inactive, remission, resolved
    verificationStatus: Optional[str] = None  # unconfirmed, provisional, differential, confirmed
    categoryCode: Optional[str] = None
    categoryDisplay: Optional[str] = None
    code: Optional[str] = None  # ICD-10 診斷碼
    codeSystem: Optional[str] = None
    display: Optional[str] = None  # 診斷名稱
    onsetDateTime: Optional[str] = None
    recordedDate: Optional[str] = None
    severity: Optional[str] = None


class MedicationInfo(BaseModel):
    """用藥紀錄資訊"""
    id: str
    status: Optional[str] = None  # active, completed, stopped, on-hold
    medicationCode: Optional[str] = None
    medicationDisplay: Optional[str] = None
    dosageText: Optional[str] = None
    route: Optional[str] = None  # 給藥途徑
    effectiveStart: Optional[str] = None
    effectiveEnd: Optional[str] = None
    reasonCode: Optional[str] = None
    reasonDisplay: Optional[str] = None


class ProcedureInfo(BaseModel):
    """處置紀錄資訊"""
    id: str
    status: Optional[str] = None
    code: Optional[str] = None
    codeSystem: Optional[str] = None
    display: Optional[str] = None
    performedDateTime: Optional[str] = None
    performedPeriodStart: Optional[str] = None
    performedPeriodEnd: Optional[str] = None
    bodySite: Optional[str] = None
    outcome: Optional[str] = None


class LabResultInfo(BaseModel):
    """檢驗結果資訊"""
    id: str
    code: str  # LOINC 代碼
    codeDisplay: Optional[str] = None  # 檢驗項目名稱
    category: Optional[str] = None  # 類別: renal, hepatic, thyroid, hematology
    value: Optional[float] = None
    valueString: Optional[str] = None  # 非數值結果
    unit: Optional[str] = None
    referenceRangeLow: Optional[float] = None
    referenceRangeHigh: Optional[float] = None
    referenceRangeText: Optional[str] = None
    interpretation: Optional[str] = None  # N(正常), L(偏低), H(偏高), LL, HH, A(異常)
    effectiveDateTime: Optional[str] = None
    isAbnormal: bool = False


class AllergyInfo(BaseModel):
    """過敏資訊"""
    id: str
    clinicalStatus: Optional[str] = None  # active, inactive, resolved
    verificationStatus: Optional[str] = None  # unconfirmed, confirmed
    type: Optional[str] = None  # allergy, intolerance
    category: Optional[str] = None  # food, medication, environment, biologic
    criticality: Optional[str] = None  # low, high, unable-to-assess
    code: Optional[str] = None  # 過敏原代碼
    display: Optional[str] = None  # 過敏原名稱
    onsetDateTime: Optional[str] = None
    recordedDate: Optional[str] = None
    reactions: list[dict[str, Any]] = []  # 反應症狀列表


class LabResultsGrouped(BaseModel):
    """分類的檢驗結果"""
    renal: list[LabResultInfo] = []      # 腎功能: Creatinine, eGFR, BUN
    hepatic: list[LabResultInfo] = []    # 肝功能: AST, ALT, Bilirubin
    thyroid: list[LabResultInfo] = []    # 甲狀腺: TSH, T4
    hematology: list[LabResultInfo] = [] # 血液: Hgb, WBC, Platelet
    other: list[LabResultInfo] = []      # 其他檢驗


class SnapshotData(BaseModel):
    """病人快照資料"""
    # 原有欄位 (保留相容性)
    conditions: list[dict[str, Any]] = []
    allergies: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []
    
    # 新增: 結構化臨床資料
    encounters: list[EncounterInfo] = []      # 就醫紀錄
    conditionList: list[ConditionInfo] = []   # 診斷/病史 (結構化)
    medications: list[MedicationInfo] = []    # 用藥紀錄
    procedures: list[ProcedureInfo] = []      # 處置紀錄
    labResults: Optional[LabResultsGrouped] = None  # 分類檢驗結果
    allergyList: list[AllergyInfo] = []       # 過敏史 (結構化)


class DoseValue(BaseModel):
    """劑量值"""
    value: float
    unit: str = "MBq"


class DoseCalculationInfo(BaseModel):
    """NA-2024 劑量計算資訊"""
    suggestedDose: float          # 建議劑量 (MBq)
    minDose: float               # 最小劑量 (MBq)
    maxDose: float               # 最大劑量 (MBq)
    formula: str                 # 計算公式說明
    reference: str = "NA-2024"   # 參考標準
    weightUsed: Optional[float] = None  # 使用的體重 (kg)
    isPediatric: bool = False    # 是否為兒童劑量計算


class DraftInfo(BaseModel):
    """草案資訊 (用於快照回應)"""
    examCode: Optional[str] = None
    radiopharmaceuticalCode: Optional[str] = None
    suggestedDose: Optional[DoseValue] = None
    override: Optional[dict[str, Any]] = None
    notes: Optional[str] = None


class RuleFlagInfo(BaseModel):
    """規則標記資訊"""
    code: str
    severity: str  # PASS, INFO, WARN, FAIL
    title: str
    explain: str
    recommendation: Optional[str] = None
    tags: list[str] = []


class RuleEvalInfo(BaseModel):
    """規則評估資訊"""
    overallSeverity: str  # PASS, INFO, WARN, FAIL
    isBatchEligible: bool
    flags: list[RuleFlagInfo]


class ReviewEventInfo(BaseModel):
    """審查事件資訊（用於顯示藥師/醫師互動歷程）"""
    id: str
    eventType: str  # RETURN, RESPONSE, SUBMIT, APPROVE, etc.
    actorSubject: str
    actingRole: str  # NM_PHYSICIAN, PHARMACIST
    payload: Optional[dict[str, Any]] = None
    createdAt: str


class PatientSnapshotResponse(BaseModel):
    """病人快照回應
    
    包含完整的案件資訊、臨床快照、候選事實、劑量計算與 CDS 評估結果
    """
    caseId: str
    patientRef: str
    serviceRequestRef: str
    status: Optional[str] = None  # 案件狀態
    snapshot: SnapshotData
    candidateFacts: list[CandidateFact]
    # 新增: 草案資訊
    draftDose: Optional[DoseValue] = None
    draft: Optional[DraftInfo] = None
    # 新增: NA-2024 劑量計算
    doseCalculation: Optional[DoseCalculationInfo] = None
    # 新增: CDS 規則評估結果
    ruleEval: Optional[RuleEvalInfo] = None
    # 新增: 審查事件歷程（藥師退回/醫師回應等）
    reviewEvents: list[ReviewEventInfo] = []


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


class ManualFactRequest(BaseModel):
    """手動輸入臨床資料請求"""
    factType: FactType
    value: Union[float, str]
    unit: Optional[str] = None


class ManualFactResponse(BaseModel):
    """手動輸入臨床資料回應"""
    caseId: str
    updatedLocalFacts: dict[str, Any]
    cds: dict[str, Any]  # RuleEval 格式

