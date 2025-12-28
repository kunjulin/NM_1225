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

// === Clinical Data Types (臨床資料類型) ===

/** 就醫紀錄類別 */
export type EncounterClass = 'AMB' | 'EMER' | 'IMP' | 'ACUTE' | 'NONAC' | 'OBSENC' | 'PRENC' | 'VR' | 'HH'

/** 就醫紀錄資訊 */
export interface EncounterInfo {
  id: string
  status?: string
  classCode?: EncounterClass      // 就醫類別: AMB(門診), EMER(急診), IMP(住院)
  classDisplay?: string           // 類別顯示名稱
  typeCode?: string
  typeDisplay?: string
  periodStart?: string            // 開始時間
  periodEnd?: string              // 結束時間
  reasonCode?: string             // 就醫原因代碼
  reasonDisplay?: string          // 就醫原因說明
  location?: string               // 地點
}

/** 診斷/病史資訊 */
export interface ConditionInfo {
  id: string
  clinicalStatus?: string         // active, recurrence, relapse, inactive, remission, resolved
  verificationStatus?: string     // unconfirmed, provisional, differential, confirmed
  categoryCode?: string
  categoryDisplay?: string
  code?: string                   // ICD-10 診斷碼
  codeSystem?: string
  display?: string                // 診斷名稱
  onsetDateTime?: string          // 發病時間
  recordedDate?: string           // 記錄時間
  severity?: string               // 嚴重程度
}

/** 用藥紀錄資訊 */
export interface MedicationInfo {
  id: string
  status?: string                 // active, completed, stopped, on-hold
  medicationCode?: string
  medicationDisplay?: string      // 藥物名稱
  dosageText?: string             // 劑量說明
  route?: string                  // 給藥途徑
  effectiveStart?: string         // 開始時間
  effectiveEnd?: string           // 結束時間
  reasonCode?: string
  reasonDisplay?: string          // 用藥原因
}

/** 處置紀錄資訊 */
export interface ProcedureInfo {
  id: string
  status?: string
  code?: string
  codeSystem?: string
  display?: string                // 處置名稱
  performedDateTime?: string      // 執行時間
  performedPeriodStart?: string
  performedPeriodEnd?: string
  bodySite?: string               // 執行部位
  outcome?: string                // 結果
}

/** 檢驗結果類別 */
export type LabCategory = 'renal' | 'hepatic' | 'thyroid' | 'hematology' | 'other'

/** 檢驗結果解讀 */
export type LabInterpretation = 'N' | 'L' | 'H' | 'LL' | 'HH' | 'A' | 'AA'

/** 檢驗結果資訊 */
export interface LabResultInfo {
  id: string
  code: string                    // LOINC 代碼
  codeDisplay?: string            // 檢驗項目名稱
  category?: LabCategory          // 類別
  value?: number                  // 數值結果
  valueString?: string            // 非數值結果
  unit?: string                   // 單位
  referenceRangeLow?: number      // 參考範圍下限
  referenceRangeHigh?: number     // 參考範圍上限
  referenceRangeText?: string     // 參考範圍文字
  interpretation?: LabInterpretation  // 解讀: N(正常), L(偏低), H(偏高)
  effectiveDateTime?: string      // 檢驗時間
  isAbnormal: boolean             // 是否異常
}

/** 分類的檢驗結果 */
export interface LabResultsGrouped {
  renal: LabResultInfo[]          // 腎功能: Creatinine, eGFR, BUN
  hepatic: LabResultInfo[]        // 肝功能: AST, ALT, Bilirubin
  thyroid: LabResultInfo[]        // 甲狀腺: TSH, T4
  hematology: LabResultInfo[]     // 血液: Hgb, WBC, Platelet
  other: LabResultInfo[]          // 其他檢驗
}

/** 過敏嚴重程度 */
export type AllergyCriticality = 'low' | 'high' | 'unable-to-assess'

/** 過敏類別 */
export type AllergyCategory = 'food' | 'medication' | 'environment' | 'biologic'

/** 過敏反應症狀 */
export interface AllergyReaction {
  severity?: string               // mild, moderate, severe
  manifestations: {
    code?: string
    display?: string
  }[]
  description?: string
}

/** 過敏資訊 */
export interface AllergyInfo {
  id: string
  clinicalStatus?: string         // active, inactive, resolved
  verificationStatus?: string     // unconfirmed, confirmed
  type?: string                   // allergy, intolerance
  category?: AllergyCategory      // 類別
  criticality?: AllergyCriticality  // 嚴重程度
  code?: string                   // 過敏原代碼
  display?: string                // 過敏原名稱
  onsetDateTime?: string          // 發生時間
  recordedDate?: string           // 記錄時間
  reactions: AllergyReaction[]    // 反應症狀列表
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

/** 病人快照資料結構 */
export interface SnapshotData {
  // 原有欄位 (保留相容性)
  conditions: unknown[]
  allergies: unknown[]
  observations: unknown[]
  documents: unknown[]
  // 基本資訊
  patientName?: string
  patientId?: string
  examCode?: string
  examDisplay?: string
  weightKg?: number
  hasAllergy?: boolean
  // 新增: 結構化臨床資料
  encounters: EncounterInfo[]         // 就醫紀錄
  conditionList: ConditionInfo[]      // 診斷/病史 (結構化)
  medications: MedicationInfo[]       // 用藥紀錄
  procedures: ProcedureInfo[]         // 處置紀錄
  labResults?: LabResultsGrouped      // 分類檢驗結果
  allergyList: AllergyInfo[]          // 過敏史 (結構化)
}

export interface PatientSnapshot {
  caseId: string
  patientRef: string
  serviceRequestRef: string
  status?: CaseStatus
  snapshot: SnapshotData
  candidateFacts: CandidateFact[]
  // 草案資訊
  draftDose?: DoseValue
  draft?: DraftInfo
  // NA-2024 劑量計算
  doseCalculation?: DoseCalculation
  // CDS 規則評估結果
  ruleEval?: RuleEval
  // 審查事件歷程（藥師退回/醫師回應等）
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

// === Auth ===

export type UserStatus = 'PENDING' | 'ACTIVE' | 'INACTIVE'

export interface AuthConfig {
  is_demo_mode: boolean
  smart_enabled: boolean
  authorization_endpoint?: string
  client_id?: string
  redirect_uri?: string
}

export interface SMARTLaunchResponse {
  authorization_url: string
  state: string
}

export interface AuthResultResponse {
  success: boolean
  subject?: string
  display_name?: string
  practitioner_ref?: string
  status?: UserStatus
  allowed_roles: string[]
  is_new_user: boolean
  error?: string
}

export interface UserInfo {
  subject: string
  display_name: string
  practitioner_ref?: string
  email?: string
  status: UserStatus
  allowed_roles: string[]
  is_admin: boolean
}

// === Admin ===

export interface UserListItem {
  id: string
  subject: string
  display_name: string
  practitioner_ref?: string
  email?: string
  status: UserStatus
  allowed_roles: string[]
  is_admin: boolean
  last_login_at?: string
  created_at: string
  updated_at: string
}

export interface UserListResponse {
  users: UserListItem[]
  total: number
  pending_count: number
}

// === Sync Log ===

export interface SyncLogItem {
  id: string
  case_id: string
  patient_name?: string
  patient_id?: string
  operation: string
  status: string
  medication_request_ref?: string
  last_error?: string
  retry_count: number
  created_at: string
  updated_at: string
}

export interface SyncLogResponse {
  logs: SyncLogItem[]
  total: number
  page: number
  page_size: number
}

// === FHIR Sync ===

export interface SyncWorklistResponse {
  fetched: number
  created: number
  skipped: number
  errors: number
  error_details: string[]
}

export interface SyncStatusResponse {
  lastSyncTime: string | null
  nextSyncIn: number | null
  isWorkerRunning: boolean
  syncIntervalSeconds: number
}

