"""
Case 相關 Schema 定義
依據 spec/03_api_contract.md 定義
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel

from app.schemas.rule_eval import RuleEval


class CaseStatus(str, Enum):
    """案件狀態
    依據 spec/01_architecture_low_coupling.md 定義的狀態機
    """
    NM_PENDING = "NM_PENDING"           # 建立自 ServiceRequest，等待核醫處理
    NM_DRAFTED = "NM_DRAFTED"           # 核醫已建立草案
    PHARM_READY = "PHARM_READY"         # 已送交藥師審查
    PHARM_IN_PROGRESS = "PHARM_IN_PROGRESS"  # 藥師已 Claim
    RETURNED = "RETURNED"               # 藥師退回核醫
    APPROVED = "APPROVED"               # 藥師核准，觸發 write-back
    SYNCING = "SYNCING"                 # 同步中
    SYNCED = "SYNCED"                   # 已同步至 FHIR
    SYNC_FAILED = "SYNC_FAILED"         # 同步失敗


class ActingRole(str, Enum):
    """操作角色"""
    NM_PHYSICIAN = "NM_PHYSICIAN"
    PHARMACIST = "PHARMACIST"
    ADMIN = "ADMIN"


class SnapshotSummary(BaseModel):
    """病人快照摘要（用於工作清單顯示）"""
    patientName: Optional[str] = None
    patientId: Optional[str] = None
    examCode: Optional[str] = None
    examDisplay: Optional[str] = None
    weightKg: Optional[float] = None
    hasAllergy: Optional[bool] = None


class WorklistItem(BaseModel):
    """工作清單項目"""
    caseId: str
    patientRef: str
    serviceRequestRef: str
    status: CaseStatus
    ownerSubject: Optional[str] = None
    snapshotSummary: SnapshotSummary
    ruleEval: RuleEval
    createdAt: datetime
    updatedAt: datetime


class WorklistGroup(BaseModel):
    """工作清單分群"""
    groupKey: str
    title: str
    count: int
    items: list[WorklistItem]


class WorklistResponse(BaseModel):
    """工作清單回應"""
    groups: list[WorklistGroup]


# === Draft 相關 ===

class DraftData(BaseModel):
    """用藥草案資料"""
    examCode: str
    radiopharmaceuticalCode: str
    suggestedDose: dict[str, Any]  # {"value": 185, "unit": "MBq"}
    override: Optional[dict[str, Any]] = None  # {"isOverride": false, "reason": ""}
    notes: Optional[str] = None


class DraftRequest(BaseModel):
    """建立/更新草案請求"""
    draft: DraftData


class DraftResponse(BaseModel):
    """草案回應"""
    caseId: str
    status: CaseStatus
    draft: DraftData
    ruleEval: RuleEval


# === Submit 相關 ===

class SubmitResponse(BaseModel):
    """送審回應"""
    caseId: str
    status: CaseStatus


# === Claim 相關 ===

class ClaimResponse(BaseModel):
    """Claim 回應"""
    caseId: str
    status: CaseStatus
    ownerSubject: str


# === Approve 相關 ===

class ApproveResponse(BaseModel):
    """核准回應"""
    caseId: str
    status: CaseStatus


# === Return 相關 ===

class ReturnReasonCode(str, Enum):
    """退回原因代碼"""
    DOSE_OUT_OF_RANGE = "DOSE_OUT_OF_RANGE"
    MISSING_DATA = "MISSING_DATA"
    MISMATCH = "MISMATCH"
    ALLERGY_CONCERN = "ALLERGY_CONCERN"
    OTHER = "OTHER"


class ReturnRequest(BaseModel):
    """退回請求"""
    returnReasonCodes: list[ReturnReasonCode]
    comment: Optional[str] = None


class ReturnResponse(BaseModel):
    """退回回應"""
    caseId: str
    status: CaseStatus


# === Respond 相關 ===

class ResponseAction(str, Enum):
    """回應動作"""
    UPDATED_DOSE = "UPDATED_DOSE"
    ADDED_MISSING_DATA = "ADDED_MISSING_DATA"
    PROVIDED_OVERRIDE_JUSTIFICATION = "PROVIDED_OVERRIDE_JUSTIFICATION"
    CANCELLED_ORDER = "CANCELLED_ORDER"


class RespondRequest(BaseModel):
    """核醫回應請求"""
    responseAction: ResponseAction
    comment: Optional[str] = None
    updatedDraft: Optional[DraftData] = None


class RespondResponse(BaseModel):
    """核醫回應結果"""
    caseId: str
    status: CaseStatus


# === Bulk Approve 相關 ===

class BulkApproveRequest(BaseModel):
    """批次核准請求"""
    caseIds: list[str]
    note: Optional[str] = None


class BulkApproveResult(BaseModel):
    """單一案件批次核准結果"""
    caseId: str
    status: Optional[CaseStatus] = None
    code: Optional[str] = None
    message: Optional[str] = None


class BulkApproveResponse(BaseModel):
    """批次核准回應"""
    ok: list[BulkApproveResult]
    failed: list[BulkApproveResult]


# === Dose Calculation 相關 (NA-2024) ===

class DoseCalculation(BaseModel):
    """NA-2024 劑量計算結果
    
    用於顯示根據 2024 北美兒童放射藥物劑量共識指引計算的建議劑量
    """
    suggestedDose: float          # 建議劑量 (MBq)
    minDose: float               # 最小劑量 (MBq)
    maxDose: float               # 最大劑量 (MBq)
    formula: str                 # 計算公式說明
    reference: str = "NA-2024"   # 參考標準
    weightUsed: Optional[float] = None  # 使用的體重 (kg)
    isPediatric: bool = False    # 是否為兒童劑量計算


# === Bulk Submit 相關 (NM 批次送審) ===

class BulkSubmitRequest(BaseModel):
    """批次送審請求"""
    caseIds: list[str]
    note: Optional[str] = None


class BulkSubmitResult(BaseModel):
    """單一案件批次送審結果"""
    caseId: str
    status: Optional[CaseStatus] = None
    code: Optional[str] = None
    message: Optional[str] = None


class BulkSubmitResponse(BaseModel):
    """批次送審回應"""
    ok: list[BulkSubmitResult]
    failed: list[BulkSubmitResult]
