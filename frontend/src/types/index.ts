/**
 * 共用型別定義
 * 對應 Backend API 回應結構
 */

// === 基礎型別 ===

export type CaseStatus = 
  | 'NM_PENDING'
  | 'NM_DRAFTED'
  | 'PHARM_READY'
  | 'PHARM_IN_PROGRESS'
  | 'RETURNED'
  | 'APPROVED'
  | 'SYNCING'
  | 'SYNCED'
  | 'SYNC_FAILED'

export type Severity = 'PASS' | 'INFO' | 'WARN' | 'FAIL'

export type ActingRole = 'NM_PHYSICIAN' | 'PHARMACIST' | 'ADMIN'

export type FactType = 'WEIGHT_KG' | 'EGFR' | 'SCR_MGDL' | 'ALLERGY_SUMMARY'

export type SourceType = 'FHIR_RESOURCE' | 'DOCUMENT_TEXT' | 'NOTE_TEXT' | 'MANUAL' | 'AUTOFILL'

export type Confidence = 'HIGH' | 'MEDIUM' | 'LOW'

export type ReturnReasonCode = 
  | 'DOSE_OUT_OF_RANGE'
  | 'MISSING_DATA'
  | 'MISMATCH'
  | 'ALLERGY_CONCERN'
  | 'OTHER'

export type ResponseAction = 
  | 'UPDATED_DOSE'
  | 'ADDED_MISSING_DATA'
  | 'PROVIDED_OVERRIDE_JUSTIFICATION'
  | 'CANCELLED_ORDER'

// === Rule Eval ===

export interface RuleFlag {
  code: string
  severity: Severity
  title: string
  explain: string
  recommendation?: string
  dataRefs?: string[]
  tags?: string[]
}

export interface RuleEval {
  overallSeverity: Severity
  isBatchEligible: boolean
  flags: RuleFlag[]
}

// === Snapshot ===

export interface SnapshotSummary {
  patientName?: string
  patientId?: string
  examCode?: string
  examDisplay?: string
  weightKg?: number
  hasAllergy?: boolean
}

export interface CandidateFact {
  factType: FactType
  value: number | string
  unit?: string
  asOf: string
  sourceType: SourceType
  sourceRef?: string
  sourceSnippet?: string
  confidence: Confidence
  extractionMethod: 'STRUCTURED' | 'PATTERN' | 'NLP'
}

// === NA-2024 Dose Calculation ===

export interface DoseCalculation {
  suggestedDose: number      // 建議劑量 (MBq)
  minDose: number           // 最小劑量 (MBq)
  maxDose: number           // 最大劑量 (MBq)
  formula: string           // 計算公式說明
  reference: string         // 參考標準 (NA-2024)
  weightUsed?: number       // 使用的體重 (kg)
  isPediatric: boolean      // 是否為兒童劑量計算
}

export interface DraftInfo {
  examCode?: string
  radiopharmaceuticalCode?: string
  suggestedDose?: DoseValue
  override?: {
    isOverride: boolean
    reason?: string
  }
  notes?: string
}

// === Review Event ===

export interface ReviewEvent {
  id: string
  eventType: 'RETURN' | 'RESPONSE' | 'SUBMIT' | 'APPROVE' | 'CLAIM'
  actorSubject: string
  actingRole: ActingRole
  payload?: {
    returnReasonCodes?: ReturnReasonCode[]
    comment?: string
    action?: ResponseAction
  }
  createdAt: string
}

export interface PatientSnapshot {
  caseId: string
  patientRef: string
  serviceRequestRef: string
  status?: CaseStatus
  snapshot: {
    conditions: unknown[]
    allergies: unknown[]
    observations: unknown[]
    documents: unknown[]
  }
  candidateFacts: CandidateFact[]
  // 新增: 草案資訊
  draftDose?: DoseValue
  draft?: DraftInfo
  // 新增: NA-2024 劑量計算
  doseCalculation?: DoseCalculation
  // 新增: CDS 規則評估結果
  ruleEval?: RuleEval
  // 新增: 審查事件歷程（藥師退回/醫師回應等）
  reviewEvents?: ReviewEvent[]
}

// === Worklist ===

export interface WorklistItem {
  caseId: string
  patientRef: string
  serviceRequestRef: string
  status: CaseStatus
  ownerSubject?: string
  snapshotSummary: SnapshotSummary
  ruleEval: RuleEval
  createdAt: string
  updatedAt: string
}

export interface WorklistGroup {
  groupKey: string
  title: string
  count: number
  items: WorklistItem[]
}

export interface WorklistResponse {
  groups: WorklistGroup[]
}

// === Draft ===

export interface DoseValue {
  value: number
  unit: string
}

export interface DraftData {
  examCode: string
  radiopharmaceuticalCode: string
  suggestedDose: DoseValue
  override?: {
    isOverride: boolean
    reason?: string
  }
  notes?: string
}

// === API Responses ===

export interface SubmitResponse {
  caseId: string
  status: CaseStatus
}

export interface ClaimResponse {
  caseId: string
  status: CaseStatus
  ownerSubject: string
}

export interface ApproveResponse {
  caseId: string
  status: CaseStatus
}

export interface ReturnResponse {
  caseId: string
  status: CaseStatus
}

export interface BulkApproveResult {
  caseId: string
  status?: CaseStatus
  code?: string
  message?: string
}

export interface BulkApproveResponse {
  ok: BulkApproveResult[]
  failed: BulkApproveResult[]
}

// === Bulk Submit (NM 批次送審) ===

export interface BulkSubmitResult {
  caseId: string
  status?: CaseStatus
  code?: string
  message?: string
}

export interface BulkSubmitResponse {
  ok: BulkSubmitResult[]
  failed: BulkSubmitResult[]
}

// === Analytics ===

export interface ReturnReasonStat {
  code: string
  count: number
  rate: number
}

export interface ResponseActionStat {
  action: string
  count: number
  rate: number
}

export interface AnalyticsSummary {
  window: {
    from_date: string
    to_date: string
  }
  totalCases: number
  inappropriateDoseRate: number
  pharmacistInterventionRate: number
  medianTAT: number
  batchApprovalRate: number
  returnReasons: ReturnReasonStat[]
  responseActions: ResponseActionStat[]
  missingDataRate: number
  overrideRate: number
}

export interface AutofillSummary {
  window: {
    from_date: string
    to_date: string
  }
  candidatesGenerated: number
  candidatesAccepted: number
  candidatesRejected: number
  acceptRate: number
  byFactType: {
    factType: string
    generated: number
    accepted: number
    rejected: number
    acceptRate: number
  }[]
}

// === Demo ===

export interface WhoAmI {
  subject: string
  actingRole: ActingRole
  appMode: string
  isDemo: boolean
}

