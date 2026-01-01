"""
Snapshot 與 Auto-fill 服務
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OrderCase, ReviewEvent
from app.schemas import (
    PatientSnapshotResponse,
    SnapshotData,
    CandidateFact,
    FactType,
    SourceType,
    Confidence,
    ExtractionMethod,
    AcceptAutoFillRequest,
    AcceptAutoFillResponse,
    RejectAutoFillRequest,
    RejectAutoFillResponse,
    ManualFactRequest,
    ManualFactResponse,
)
from app.schemas.snapshot import (
    DoseValue,
    DoseCalculationInfo,
    DraftInfo,
    RuleFlagInfo,
    RuleEvalInfo,
    ReviewEventInfo,
    EncounterInfo,
    ConditionInfo,
    MedicationInfo,
    ProcedureInfo,
    LabResultInfo,
    LabResultsGrouped,
    AllergyInfo,
)
from app.services.auth_service import CurrentUser
from app.rules.engine import RuleEngine
from app.fhir.client import FHIRClient


class SnapshotService:
    """Snapshot 服務"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rule_engine = RuleEngine()
        self.fhir_client = FHIRClient()
    
    async def get_snapshot(
        self, 
        case_id: str, 
        refresh: bool = False
    ) -> PatientSnapshotResponse:
        """取得病人快照與自動填入候選值
        
        包含:
        - 臨床資料快照 (conditions, allergies, observations, documents)
        - 自動填入候選值
        - 目前草案劑量
        - NA-2024 劑量計算結果
        - CDS 規則評估結果
        """
        case = await self._get_case(case_id)
        
        # 若需要重新擷取或快照不存在
        if refresh or not case.snapshot_json:
            await self._refresh_snapshot(case)
        else:
            # 檢查快照是否只包含基本資料（缺少臨床資料）
            snapshot_data = json.loads(case.snapshot_json or "{}")
            has_clinical_data = (
                snapshot_data.get("encounters") or
                snapshot_data.get("conditionList") or
                snapshot_data.get("medications") or
                snapshot_data.get("procedures") or
                snapshot_data.get("labResults") or
                snapshot_data.get("allergyList")
            )
            
            # 如果快照存在但沒有臨床資料，自動重新建立完整快照
            if not has_clinical_data:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Snapshot for case {case_id} exists but lacks clinical data, refreshing...")
                await self._refresh_snapshot(case)
        
        # 從現有快照中提取並填充缺少的 local_facts（如果還沒有）
        await self._extract_facts_from_snapshot(case)
        
        # 解析快照
        snapshot_data = json.loads(case.snapshot_json or "{}")
        snapshot = self._parse_snapshot_data(snapshot_data)
        
        # 不再產生候選值（已移除自動填入功能）
        candidate_facts = []
        
        # 解析草案資訊
        draft_data = json.loads(case.draft_json or "{}")
        draft_info = None
        draft_dose = None
        
        if draft_data:
            suggested_dose = draft_data.get("suggestedDose", {})
            if suggested_dose and suggested_dose.get("value"):
                draft_dose = DoseValue(
                    value=suggested_dose.get("value"),
                    unit=suggested_dose.get("unit", "MBq")
                )
            
            draft_info = DraftInfo(
                examCode=draft_data.get("examCode"),
                radiopharmaceuticalCode=draft_data.get("radiopharmaceuticalCode"),
                suggestedDose=draft_dose,
                override=draft_data.get("override"),
                notes=draft_data.get("notes")
            )
        
        # 取得 NA-2024 劑量計算
        dose_calc_result = self.rule_engine.get_dose_calculation_for_case(case)
        dose_calculation = None
        if dose_calc_result:
            dose_calculation = DoseCalculationInfo(
                suggestedDose=dose_calc_result.suggested_dose,
                minDose=dose_calc_result.min_dose,
                maxDose=dose_calc_result.max_dose,
                formula=dose_calc_result.formula,
                reference=dose_calc_result.reference,
                weightUsed=dose_calc_result.weight_used,
                isPediatric=dose_calc_result.is_pediatric
            )
        
        # 執行 CDS 規則評估
        rule_eval = self.rule_engine.evaluate(case)
        rule_eval_info = RuleEvalInfo(
            overallSeverity=rule_eval.overallSeverity.value,
            isBatchEligible=rule_eval.isBatchEligible,
            flags=[
                RuleFlagInfo(
                    code=f.code,
                    severity=f.severity.value,
                    title=f.title,
                    explain=f.explain,
                    recommendation=f.recommendation,
                    tags=f.tags or []
                )
                for f in rule_eval.flags
            ]
        )
        
        # 查詢審查事件歷程（藥師退回、醫師回應等）
        review_events = await self._get_review_events(case_id)
        
        # 確保所有變更都被寫入資料庫（包括 _extract_facts_from_snapshot 的變更）
        await self.db.flush()
        
        return PatientSnapshotResponse(
            caseId=case_id,
            patientRef=case.patient_ref,
            serviceRequestRef=case.service_request_ref,
            status=case.status,
            snapshot=snapshot,
            candidateFacts=candidate_facts,
            draftDose=draft_dose,
            draft=draft_info,
            doseCalculation=dose_calculation,
            ruleEval=rule_eval_info,
            reviewEvents=review_events,
        )
    
    async def accept_autofill(
        self, 
        case_id: str, 
        request: AcceptAutoFillRequest,
        current_user: CurrentUser
    ) -> AcceptAutoFillResponse:
        """接受自動填入候選值"""
        case = await self._get_case(case_id)
        
        # 更新 local_facts
        local_facts = json.loads(case.local_facts_json or "{}")
        
        for fact in request.facts:
            fact_key = self._fact_type_to_key(fact.factType)
            local_facts[fact_key] = {
                "value": fact.value,
                "unit": fact.unit,
                "asOf": fact.asOf.isoformat(),
                "source": SourceType.AUTOFILL.value,
                "sourceRef": fact.sourceRef,
                "confidence": fact.confidence.value,
                "enteredBy": current_user.subject,
            }
        
        case.local_facts_json = json.dumps(local_facts)
        case.updated_at = datetime.now(timezone.utc).isoformat()
        
        # 建立事件
        event = ReviewEvent(
            id=str(uuid.uuid4()),
            case_id=case_id,
            event_type="AUTOFILL_ACCEPT",
            actor_subject=current_user.subject,
            acting_role=current_user.acting_role.value,
            payload_json=json.dumps({
                "facts": [f.model_dump() for f in request.facts],
                "reason": request.reason
            }, default=str),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(event)
        
        await self.db.commit()
        
        # 重新評估規則
        rule_eval = self.rule_engine.evaluate(case)
        
        return AcceptAutoFillResponse(
            caseId=case_id,
            updatedLocalFacts=local_facts,
            cds=rule_eval.model_dump()
        )
    
    async def reject_autofill(
        self, 
        case_id: str, 
        request: RejectAutoFillRequest,
        current_user: CurrentUser
    ) -> RejectAutoFillResponse:
        """拒絕自動填入候選值（記錄稽核）"""
        case = await self._get_case(case_id)
        
        # 建立事件
        event = ReviewEvent(
            id=str(uuid.uuid4()),
            case_id=case_id,
            event_type="AUTOFILL_REJECT",
            actor_subject=current_user.subject,
            acting_role=current_user.acting_role.value,
            payload_json=json.dumps({
                "rejections": [r.model_dump() for r in request.rejections]
            }, default=str),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(event)
        
        await self.db.commit()
        
        return RejectAutoFillResponse(
            caseId=case_id,
            rejected=True
        )
    
    async def _get_case(self, case_id: str) -> OrderCase:
        """取得案件"""
        result = await self.db.execute(
            select(OrderCase).where(OrderCase.id == case_id)
        )
        case = result.scalar_one_or_none()
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case not found: {case_id}"
            )
        
        return case
    
    async def _get_review_events(self, case_id: str) -> list[ReviewEventInfo]:
        """取得案件的審查事件歷程
        
        只返回與藥師/醫師互動相關的事件（RETURN, RESPONSE, SUBMIT, APPROVE 等）
        """
        result = await self.db.execute(
            select(ReviewEvent)
            .where(ReviewEvent.case_id == case_id)
            .where(ReviewEvent.event_type.in_(['RETURN', 'RESPONSE', 'SUBMIT', 'APPROVE', 'CLAIM']))
            .order_by(ReviewEvent.created_at.asc())
        )
        events = result.scalars().all()
        
        review_events = []
        for event in events:
            payload = None
            if event.payload_json:
                try:
                    payload = json.loads(event.payload_json)
                except:
                    pass
            
            review_events.append(ReviewEventInfo(
                id=event.id,
                eventType=event.event_type,
                actorSubject=event.actor_subject,
                actingRole=event.acting_role,
                payload=payload,
                createdAt=event.created_at,
            ))
        
        return review_events
    
    async def _refresh_snapshot(self, case: OrderCase):
        """從 FHIR 重新擷取完整臨床快照
        
        擷取內容包含:
        - 基本病人資訊
        - ServiceRequest 檢查資訊 (examCode, examDisplay)
        - 就醫紀錄 (Encounter)
        - 診斷/病史 (Condition)
        - 用藥紀錄 (MedicationStatement)
        - 處置紀錄 (Procedure)
        - 過敏史 (AllergyIntolerance)
        - 檢驗資料 (Observation) - 含腎功能、肝功能、甲狀腺、血液
        """
        try:
            # 取得 Patient 基本資訊
            patient = await self.fhir_client.get_patient(case.patient_ref)
            
            # 取得 ServiceRequest 以提取檢查資訊和 TW Core 欄位
            exam_code = None
            exam_display = None
            occurrence_datetime = None
            requester_display = None
            reason_code_display = None
            
            if case.service_request_ref:
                try:
                    service_request = await self.fhir_client.get_service_request(case.service_request_ref)
                    if service_request:
                        code = service_request.get("code", {})
                        coding = code.get("coding", [{}])[0] if code.get("coding") else {}
                        snomed_code = coding.get("code", "")
                        exam_display = coding.get("display", "") or code.get("text", "")
                        
                        # 將 SNOMED CT 代碼映射到系統 examCode
                        # SNOMED CT 到系統 examCode 的映射表（對應 rules_config.yaml）
                        snomed_to_exam_code = {
                            "77477000": "BONE_SCAN",      # Bone scan (骨骼掃描)
                            "241620005": "MAG3",          # Renal scan (腎功能掃描)
                            "241520004": "DMSA",          # DMSA scan (腎臟皮質掃描)
                            "312124007": "MIBG",          # MIBG scan
                            "78800008": "FDG_PET",        # FDG PET scan (葡萄糖正子造影)
                            "432100008": "DTPA",          # DTPA scan (腎絲球過濾率掃描) - 使用 GFR measurement code
                            "432100009": "NaF_PET",       # NaF PET scan (氟化鈉正子造影)
                            "432100010": "DOTATATE",      # DOTATATE PET scan
                        }
                        
                        exam_code = snomed_to_exam_code.get(snomed_code, snomed_code)  # 如果沒有映射，使用原始代碼
                        
                        # 提取 TW Core ServiceRequest 相關欄位
                        # 1. occurrenceDateTime - 期望執行時間
                        occurrence_datetime = service_request.get("occurrenceDateTime")
                        
                        # 2. requester - 開單醫師
                        requester = service_request.get("requester", {})
                        requester_display = requester.get("display", "")
                        if not requester_display and requester.get("reference"):
                            # 如果沒有 display，嘗試從 reference 取得名稱（可選）
                            requester_display = requester.get("reference", "").split("/")[-1]
                        
                        # 3. reasonCode - 適應症/診斷依據
                        reason_codes = service_request.get("reasonCode", [])
                        if reason_codes:
                            first_reason = reason_codes[0]
                            # 優先使用 text，其次使用 coding[].display
                            reason_code_display = first_reason.get("text", "")
                            if not reason_code_display:
                                codings = first_reason.get("coding", [])
                                if codings:
                                    reason_code_display = codings[0].get("display", "")
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Failed to fetch ServiceRequest {case.service_request_ref}: {e}")
            
            # 並行取得各類臨床資料
            weight_obs = await self.fhir_client.get_latest_weight(case.patient_ref)
            allergies = await self.fhir_client.get_allergies(case.patient_ref)
            encounters = await self.fhir_client.get_encounters(case.patient_ref)
            conditions = await self.fhir_client.get_conditions(case.patient_ref)
            medications = await self.fhir_client.get_medications(case.patient_ref)
            procedures = await self.fhir_client.get_procedures(case.patient_ref)
            
            # 取得重要檢驗資料 (LOINC codes)
            lab_codes = [
                "2160-0",   # Creatinine (血清肌酸酐)
                "33914-3",  # eGFR (腎絲球過濾率)
                "3094-0",   # BUN (血中尿素氮)
                "1742-6",   # ALT (丙氨酸轉氨酶)
                "1920-8",   # AST (天門冬氨酸轉氨酶)
                "1975-2",   # Bilirubin Total (總膽紅素)
                "3016-3",   # TSH (促甲狀腺激素)
                "3026-2",   # T4 Free (游離甲狀腺素)
                "718-7",    # Hemoglobin (血紅素)
                "6690-2",   # WBC (白血球)
                "777-3",    # Platelet (血小板)
            ]
            lab_results = await self.fhir_client.get_lab_by_codes(case.patient_ref, lab_codes)
            
            # 組合快照 (保留原有結構以維持相容性)
            patient_name = "Unknown"
            if patient and patient.get("name"):
                name_obj = patient["name"][0]
                patient_name = name_obj.get("text") or f"{name_obj.get('family', '')} {' '.join(name_obj.get('given', []))}"
            
            # 保留舊快照中的 TW Core ServiceRequest 欄位（如果新資料沒有）
            old_snapshot_data = json.loads(case.snapshot_json or "{}") if case.snapshot_json else {}
            
            snapshot = {
                # 原有欄位
                "patientName": patient_name,
                "patientId": case.patient_ref,
                "examCode": exam_code,  # 從 ServiceRequest 提取
                "examDisplay": exam_display,  # 從 ServiceRequest 提取
                "observations": [weight_obs] if weight_obs else [],
                "allergies": allergies,
                "conditions": conditions,
                "documents": [],
                
                # 新增: 結構化臨床資料
                "encounters": self._parse_encounters(encounters),
                "conditionList": self._parse_conditions(conditions),
                "medications": self._parse_medications(medications),
                "procedures": self._parse_procedures(procedures),
                "labResults": self._parse_lab_results(lab_results),
                "allergyList": self._parse_allergies(allergies),
                
                # TW Core ServiceRequest 相關欄位（優先使用新提取的，否則保留舊的）
                "occurrenceDateTime": occurrence_datetime or old_snapshot_data.get("occurrenceDateTime"),
                "requesterDisplay": requester_display or old_snapshot_data.get("requesterDisplay"),
                "reasonCodeDisplay": reason_code_display or old_snapshot_data.get("reasonCodeDisplay"),
            }
            
            if weight_obs:
                snapshot["weightKg"] = weight_obs.get("valueQuantity", {}).get("value")
            
            snapshot["hasAllergy"] = len(allergies) > 0
            
            case.snapshot_json = json.dumps(snapshot)
            
            # 自動從 FHIR 資料提取關鍵臨床資料並加入到 local_facts（如果還沒有手動輸入的資料）
            original_local_facts_json = case.local_facts_json
            local_facts = json.loads(original_local_facts_json or "{}")
            local_facts_updated = False
            
            # 自動提取體重（如果還沒有手動輸入）
            if "weightKg" not in local_facts and weight_obs:
                value_quantity = weight_obs.get("valueQuantity", {})
                weight_value = value_quantity.get("value")
                weight_unit = value_quantity.get("unit")
                effective_date = weight_obs.get("effectiveDateTime")
                
                if weight_value is not None:
                    local_facts["weightKg"] = {
                        "value": weight_value,
                        "unit": weight_unit or "kg",
                        "asOf": effective_date or datetime.now(timezone.utc).isoformat(),
                        "source": SourceType.FHIR_RESOURCE.value,
                        "sourceRef": weight_obs.get("id"),
                    }
                    local_facts_updated = True
            
            # 自動提取 eGFR（如果還沒有手動輸入）
            if "eGFR" not in local_facts:
                # 從 lab_results 中提取最新的 eGFR (LOINC 33914-3)
                egfr_observations = lab_results.get("33914-3", [])
                if egfr_observations:
                    # 取最新的 eGFR（已經按日期排序，第一個是最新的）
                    latest_egfr = egfr_observations[0]
                    value_quantity = latest_egfr.get("valueQuantity", {})
                    egfr_value = value_quantity.get("value")
                    egfr_unit = value_quantity.get("unit")
                    effective_date = latest_egfr.get("effectiveDateTime")
                    
                    if egfr_value is not None:
                        local_facts["eGFR"] = {
                            "value": egfr_value,
                            "unit": egfr_unit,
                            "asOf": effective_date or datetime.now(timezone.utc).isoformat(),
                            "source": SourceType.FHIR_RESOURCE.value,
                            "sourceRef": latest_egfr.get("id"),
                        }
                        local_facts_updated = True
            
            # 如果有更新 local_facts，保存到資料庫
            if local_facts_updated:
                case.local_facts_json = json.dumps(local_facts)
                await self.db.flush()
            
            case.updated_at = datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            # 擷取失敗時保留舊快照，記錄錯誤
            import logging
            logging.getLogger(__name__).error(f"Failed to refresh snapshot for case {case.id}: {e}")
    
    async def _extract_facts_from_snapshot(self, case: OrderCase):
        """從現有 snapshot 中提取並填充缺少的 local_facts
        
        這個方法用於處理已經存在快照但 local_facts 中缺少資料的情況
        """
        try:
            snapshot_data = json.loads(case.snapshot_json or "{}")
            local_facts = json.loads(case.local_facts_json or "{}")
            local_facts_updated = False
            
            # 從 snapshot 的 labResults 中提取 eGFR（如果 local_facts 中還沒有）
            if "eGFR" not in local_facts:
                lab_results_data = snapshot_data.get("labResults", {})
                if lab_results_data:
                    # labResults 是分類的結構 {renal: [], hepatic: [], ...}
                    renal_labs = lab_results_data.get("renal", [])
                    # 尋找 code 為 "33914-3" 的 eGFR 資料
                    # 找出所有 eGFR 資料，然後選擇最新的（按 effectiveDateTime 排序）
                    egfr_labs = [lab for lab in renal_labs if lab.get("code") == "33914-3"]
                    if egfr_labs:
                        # 按日期排序（最新的在前），如果沒有日期則放在最後
                        egfr_labs.sort(
                            key=lambda x: x.get("effectiveDateTime") or "",
                            reverse=True
                        )
                        latest_egfr = egfr_labs[0]
                        egfr_value = latest_egfr.get("value")
                        egfr_unit = latest_egfr.get("unit")
                        effective_date = latest_egfr.get("effectiveDateTime")
                        lab_id = latest_egfr.get("id")
                        
                        if egfr_value is not None:
                            local_facts["eGFR"] = {
                                "value": egfr_value,
                                "unit": egfr_unit,
                                "asOf": effective_date or datetime.now(timezone.utc).isoformat(),
                                "source": SourceType.FHIR_RESOURCE.value,
                                "sourceRef": lab_id,
                            }
                            local_facts_updated = True
            
            # 從 snapshot 中提取體重（如果 local_facts 中還沒有或值為空）
            weight_in_local_facts = local_facts.get("weightKg")
            weight_value = None
            if isinstance(weight_in_local_facts, dict):
                weight_value = weight_in_local_facts.get("value")
            
            if not weight_value:  # 如果 local_facts 中沒有體重或值為空
                weight_kg = snapshot_data.get("weightKg")
                if weight_kg is not None:
                    # 從 observations 中找到體重 observation 以取得更多資訊
                    observations = snapshot_data.get("observations", [])
                    weight_obs = None
                    if observations:
                        # 尋找體重 observation（LOINC 29463-7）
                        for obs in observations:
                            code = obs.get("code", {})
                            codings = code.get("coding", [])
                            for coding in codings:
                                if coding.get("code") == "29463-7":
                                    weight_obs = obs
                                    break
                            if weight_obs:
                                break
                    
                    if weight_obs:
                        effective_date = weight_obs.get("effectiveDateTime")
                        obs_id = weight_obs.get("id")
                        value_quantity = weight_obs.get("valueQuantity", {})
                        weight_unit = value_quantity.get("unit", "kg")
                    else:
                        effective_date = None
                        obs_id = None
                        weight_unit = "kg"
                    
                    local_facts["weightKg"] = {
                        "value": weight_kg,
                        "unit": weight_unit,
                        "asOf": effective_date or datetime.now(timezone.utc).isoformat(),
                        "source": SourceType.FHIR_RESOURCE.value,
                        "sourceRef": obs_id,
                    }
                    local_facts_updated = True
            
            # 如果有更新 local_facts，保存到資料庫
            if local_facts_updated:
                case.local_facts_json = json.dumps(local_facts)
                await self.db.flush()
        except Exception as e:
            # 提取失敗不影響主流程，只記錄錯誤
            import logging
            logging.getLogger(__name__).warning(f"Failed to extract facts from snapshot for case {case.id}: {e}")
    
    def _parse_snapshot_data(self, snapshot_data: dict) -> SnapshotData:
        """解析快照資料為結構化格式"""
        # 解析分類檢驗結果
        lab_results_data = snapshot_data.get("labResults")
        lab_results = None
        if lab_results_data:
            lab_results = LabResultsGrouped(
                renal=[LabResultInfo(**r) for r in lab_results_data.get("renal", [])],
                hepatic=[LabResultInfo(**r) for r in lab_results_data.get("hepatic", [])],
                thyroid=[LabResultInfo(**r) for r in lab_results_data.get("thyroid", [])],
                hematology=[LabResultInfo(**r) for r in lab_results_data.get("hematology", [])],
                other=[LabResultInfo(**r) for r in lab_results_data.get("other", [])],
            )
        
        return SnapshotData(
            # 原有欄位
            conditions=snapshot_data.get("conditions", []),
            allergies=snapshot_data.get("allergies", []),
            observations=snapshot_data.get("observations", []),
            documents=snapshot_data.get("documents", []),
            # 新增結構化欄位
            encounters=[EncounterInfo(**e) for e in snapshot_data.get("encounters", [])],
            conditionList=[ConditionInfo(**c) for c in snapshot_data.get("conditionList", [])],
            medications=[MedicationInfo(**m) for m in snapshot_data.get("medications", [])],
            procedures=[ProcedureInfo(**p) for p in snapshot_data.get("procedures", [])],
            labResults=lab_results,
            allergyList=[AllergyInfo(**a) for a in snapshot_data.get("allergyList", [])],
            # TW Core ServiceRequest 相關欄位
            occurrenceDateTime=snapshot_data.get("occurrenceDateTime"),
            requesterDisplay=snapshot_data.get("requesterDisplay"),
            reasonCodeDisplay=snapshot_data.get("reasonCodeDisplay"),
            # 病人基本資料
            weightKg=snapshot_data.get("weightKg"),
            examCode=snapshot_data.get("examCode"),
            examDisplay=snapshot_data.get("examDisplay"),
            patientId=snapshot_data.get("patientId"),
            patientName=snapshot_data.get("patientName"),
        )
    
    def _parse_encounters(self, encounters: list[dict]) -> list[dict]:
        """解析就醫紀錄 FHIR 資源"""
        result = []
        for enc in encounters:
            class_info = enc.get("class", {})
            type_info = enc.get("type", [{}])[0] if enc.get("type") else {}
            type_coding = type_info.get("coding", [{}])[0] if type_info.get("coding") else {}
            reason = enc.get("reasonCode", [{}])[0] if enc.get("reasonCode") else {}
            reason_coding = reason.get("coding", [{}])[0] if reason.get("coding") else {}
            period = enc.get("period", {})
            location = enc.get("location", [{}])[0] if enc.get("location") else {}
            
            result.append({
                "id": enc.get("id", ""),
                "status": enc.get("status"),
                "classCode": class_info.get("code"),
                "classDisplay": class_info.get("display") or self._get_encounter_class_display(class_info.get("code")),
                "typeCode": type_coding.get("code"),
                "typeDisplay": type_coding.get("display"),
                "periodStart": period.get("start"),
                "periodEnd": period.get("end"),
                "reasonCode": reason_coding.get("code"),
                "reasonDisplay": reason_coding.get("display") or reason.get("text"),
                "location": location.get("location", {}).get("display"),
            })
        return result
    
    def _get_encounter_class_display(self, code: Optional[str]) -> Optional[str]:
        """取得就醫類別顯示名稱"""
        mapping = {
            "AMB": "門診",
            "EMER": "急診",
            "IMP": "住院",
            "ACUTE": "急性照護",
            "NONAC": "非急性照護",
            "OBSENC": "產科照護",
            "PRENC": "術前評估",
            "VR": "虛擬",
            "HH": "居家照護",
        }
        return mapping.get(code) if code else None
    
    def _parse_conditions(self, conditions: list[dict]) -> list[dict]:
        """解析診斷/病史 FHIR 資源"""
        result = []
        for cond in conditions:
            clinical_status = cond.get("clinicalStatus", {}).get("coding", [{}])[0].get("code")
            verification_status = cond.get("verificationStatus", {}).get("coding", [{}])[0].get("code")
            category = cond.get("category", [{}])[0] if cond.get("category") else {}
            category_coding = category.get("coding", [{}])[0] if category.get("coding") else {}
            code_info = cond.get("code", {})
            code_coding = code_info.get("coding", [{}])[0] if code_info.get("coding") else {}
            severity = cond.get("severity", {}).get("coding", [{}])[0].get("display") if cond.get("severity") else None
            
            result.append({
                "id": cond.get("id", ""),
                "clinicalStatus": clinical_status,
                "verificationStatus": verification_status,
                "categoryCode": category_coding.get("code"),
                "categoryDisplay": category_coding.get("display"),
                "code": code_coding.get("code"),
                "codeSystem": code_coding.get("system"),
                "display": code_coding.get("display") or code_info.get("text"),
                "onsetDateTime": cond.get("onsetDateTime"),
                "recordedDate": cond.get("recordedDate"),
                "severity": severity,
            })
        return result
    
    def _parse_medications(self, medications: list[dict]) -> list[dict]:
        """解析用藥紀錄 FHIR 資源"""
        result = []
        for med in medications:
            medication = med.get("medicationCodeableConcept", {})
            med_coding = medication.get("coding", [{}])[0] if medication.get("coding") else {}
            dosage = med.get("dosage", [{}])[0] if med.get("dosage") else {}
            route = dosage.get("route", {}).get("coding", [{}])[0] if dosage.get("route") else {}
            reason = med.get("reasonCode", [{}])[0] if med.get("reasonCode") else {}
            reason_coding = reason.get("coding", [{}])[0] if reason.get("coding") else {}
            effective = med.get("effectivePeriod", {})
            
            result.append({
                "id": med.get("id", ""),
                "status": med.get("status"),
                "medicationCode": med_coding.get("code"),
                "medicationDisplay": med_coding.get("display") or medication.get("text"),
                "dosageText": dosage.get("text"),
                "route": route.get("display"),
                "effectiveStart": effective.get("start") or med.get("effectiveDateTime"),
                "effectiveEnd": effective.get("end"),
                "reasonCode": reason_coding.get("code"),
                "reasonDisplay": reason_coding.get("display") or reason.get("text"),
            })
        return result
    
    def _parse_procedures(self, procedures: list[dict]) -> list[dict]:
        """解析處置紀錄 FHIR 資源"""
        result = []
        for proc in procedures:
            code_info = proc.get("code", {})
            code_coding = code_info.get("coding", [{}])[0] if code_info.get("coding") else {}
            body_site = proc.get("bodySite", [{}])[0] if proc.get("bodySite") else {}
            body_site_coding = body_site.get("coding", [{}])[0] if body_site.get("coding") else {}
            outcome = proc.get("outcome", {}).get("coding", [{}])[0] if proc.get("outcome") else {}
            performed = proc.get("performedPeriod", {})
            
            result.append({
                "id": proc.get("id", ""),
                "status": proc.get("status"),
                "code": code_coding.get("code"),
                "codeSystem": code_coding.get("system"),
                "display": code_coding.get("display") or code_info.get("text"),
                "performedDateTime": proc.get("performedDateTime"),
                "performedPeriodStart": performed.get("start"),
                "performedPeriodEnd": performed.get("end"),
                "bodySite": body_site_coding.get("display") or body_site.get("text"),
                "outcome": outcome.get("display"),
            })
        return result
    
    def _parse_lab_results(self, lab_results: dict[str, list[dict]]) -> dict:
        """解析檢驗結果並分類
        
        Args:
            lab_results: 以 LOINC 代碼為 key 的檢驗資料字典
        
        Returns:
            分類後的檢驗結果
        """
        # LOINC 代碼對應的檢驗項目資訊
        lab_info = {
            "2160-0": {"display": "Creatinine (肌酸酐)", "category": "renal"},
            "33914-3": {"display": "eGFR (腎絲球過濾率)", "category": "renal"},
            "3094-0": {"display": "BUN (血中尿素氮)", "category": "renal"},
            "1742-6": {"display": "ALT (丙氨酸轉氨酶)", "category": "hepatic"},
            "1920-8": {"display": "AST (天門冬氨酸轉氨酶)", "category": "hepatic"},
            "1975-2": {"display": "Bilirubin Total (總膽紅素)", "category": "hepatic"},
            "3016-3": {"display": "TSH (促甲狀腺激素)", "category": "thyroid"},
            "3026-2": {"display": "T4 Free (游離甲狀腺素)", "category": "thyroid"},
            "718-7": {"display": "Hemoglobin (血紅素)", "category": "hematology"},
            "6690-2": {"display": "WBC (白血球)", "category": "hematology"},
            "777-3": {"display": "Platelet (血小板)", "category": "hematology"},
        }
        
        categorized = {
            "renal": [],
            "hepatic": [],
            "thyroid": [],
            "hematology": [],
            "other": [],
        }
        
        for loinc_code, observations in lab_results.items():
            info = lab_info.get(loinc_code, {"display": loinc_code, "category": "other"})
            category = info["category"]
            
            for obs in observations:
                # 解析數值
                value = None
                value_string = None
                unit = None
                
                if "valueQuantity" in obs:
                    vq = obs["valueQuantity"]
                    value = vq.get("value")
                    unit = vq.get("unit") or vq.get("code")
                elif "valueString" in obs:
                    value_string = obs["valueString"]
                elif "valueCodeableConcept" in obs:
                    value_string = obs["valueCodeableConcept"].get("text") or \
                                   obs["valueCodeableConcept"].get("coding", [{}])[0].get("display")
                
                # 解析參考範圍
                ref_range = obs.get("referenceRange", [{}])[0] if obs.get("referenceRange") else {}
                ref_low = ref_range.get("low", {}).get("value")
                ref_high = ref_range.get("high", {}).get("value")
                ref_text = ref_range.get("text")
                
                # 解析解讀
                interpretation = None
                is_abnormal = False
                if obs.get("interpretation"):
                    interp_coding = obs["interpretation"][0].get("coding", [{}])[0]
                    interpretation = interp_coding.get("code")
                    # 非正常值判斷
                    is_abnormal = interpretation in ["L", "H", "LL", "HH", "A", "AA"]
                
                lab_entry = {
                    "id": obs.get("id", ""),
                    "code": loinc_code,
                    "codeDisplay": info["display"],
                    "category": category,
                    "value": value,
                    "valueString": value_string,
                    "unit": unit,
                    "referenceRangeLow": ref_low,
                    "referenceRangeHigh": ref_high,
                    "referenceRangeText": ref_text,
                    "interpretation": interpretation,
                    "effectiveDateTime": obs.get("effectiveDateTime"),
                    "isAbnormal": is_abnormal,
                }
                
                categorized[category].append(lab_entry)
        
        return categorized
    
    def _parse_allergies(self, allergies: list[dict]) -> list[dict]:
        """解析過敏資訊 FHIR 資源"""
        result = []
        for allergy in allergies:
            clinical_status = allergy.get("clinicalStatus", {}).get("coding", [{}])[0].get("code")
            verification_status = allergy.get("verificationStatus", {}).get("coding", [{}])[0].get("code")
            code_info = allergy.get("code", {})
            code_coding = code_info.get("coding", [{}])[0] if code_info.get("coding") else {}
            
            # 解析反應症狀
            reactions = []
            for reaction in allergy.get("reaction", []):
                manifestations = []
                for manifest in reaction.get("manifestation", []):
                    coding = manifest.get("coding", [{}])[0] if manifest.get("coding") else {}
                    manifestations.append({
                        "code": coding.get("code"),
                        "display": coding.get("display") or manifest.get("text"),
                    })
                reactions.append({
                    "severity": reaction.get("severity"),
                    "manifestations": manifestations,
                    "description": reaction.get("description"),
                })
            
            result.append({
                "id": allergy.get("id", ""),
                "clinicalStatus": clinical_status,
                "verificationStatus": verification_status,
                "type": allergy.get("type"),
                "category": allergy.get("category", [None])[0] if allergy.get("category") else None,
                "criticality": allergy.get("criticality"),
                "code": code_coding.get("code"),
                "display": code_coding.get("display") or code_info.get("text"),
                "onsetDateTime": allergy.get("onsetDateTime"),
                "recordedDate": allergy.get("recordedDate"),
                "reactions": reactions,
            })
        return result
    
    
    def _fact_type_to_key(self, fact_type: FactType) -> str:
        """轉換 FactType 為 local_facts key"""
        mapping = {
            FactType.WEIGHT_KG: "weightKg",
            FactType.EGFR: "eGFR",
            FactType.SCR_MGDL: "scrMgdL",
            FactType.ALLERGY_SUMMARY: "allergySummary",
        }
        return mapping.get(fact_type, fact_type.value.lower())
    
    async def save_manual_fact(
        self,
        case_id: str,
        request: ManualFactRequest,
        current_user: CurrentUser
    ) -> ManualFactResponse:
        """手動輸入臨床資料
        
        允許醫師手動輸入缺少的臨床資料（如體重）
        """
        case = await self._get_case(case_id)
        
        # 更新 local_facts
        local_facts = json.loads(case.local_facts_json or "{}")
        
        fact_key = self._fact_type_to_key(request.factType)
        local_facts[fact_key] = {
            "value": request.value,
            "unit": request.unit,
            "asOf": datetime.now(timezone.utc).isoformat(),
            "source": SourceType.MANUAL.value,
            "enteredBy": current_user.subject,
        }
        
        case.local_facts_json = json.dumps(local_facts)
        case.updated_at = datetime.now(timezone.utc).isoformat()
        
        # 建立事件
        event = ReviewEvent(
            id=str(uuid.uuid4()),
            case_id=case_id,
            event_type="MANUAL_FACT_ENTRY",
            actor_subject=current_user.subject,
            acting_role=current_user.acting_role.value,
            payload_json=json.dumps({
                "factType": request.factType.value,
                "value": request.value,
                "unit": request.unit,
            }, default=str),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(event)
        
        # 如果輸入的是體重，且現在有檢查代碼，自動重新計算劑量並更新草案
        if request.factType.value == "WEIGHT_KG":
            snapshot_data = json.loads(case.snapshot_json or "{}")
            draft_data = json.loads(case.draft_json or "{}")
            
            # 取得檢查代碼
            exam_code = draft_data.get("examCode") or snapshot_data.get("examCode")
            weight_kg = request.value
            
            if exam_code:
                # 重新計算 NA-2024 劑量
                dose_calc = self.rule_engine.calculate_na2024_dose(exam_code, weight_kg)
                
                if dose_calc:
                    # 更新草案劑量
                    if not draft_data:
                        draft_data = {}
                    
                    draft_data["examCode"] = exam_code
                    draft_data["radiopharmaceuticalCode"] = exam_code
                    draft_data["suggestedDose"] = {
                        "value": dose_calc.suggested_dose,
                        "unit": "MBq"
                    }
                    # 保留原有的 override 設定
                    if "override" not in draft_data:
                        draft_data["override"] = {"isOverride": False}
                    
                    case.draft_json = json.dumps(draft_data, ensure_ascii=False)
        
        await self.db.commit()
        
        # 重新評估規則（在更新草案後）
        rule_eval = self.rule_engine.evaluate(case)
        
        # 如果 CDS 評估變為 PASS，且狀態為 NM_PENDING，自動更新為 NM_DRAFTED
        from app.models.order_case import CaseStatus
        from app.rules.engine import Severity
        if rule_eval.overallSeverity == Severity.PASS and case.status == CaseStatus.NM_PENDING.value:
            case.status = CaseStatus.NM_DRAFTED.value
            case.updated_at = datetime.now(timezone.utc).isoformat()
            await self.db.commit()
        
        return ManualFactResponse(
            caseId=case_id,
            updatedLocalFacts=local_facts,
            cds=rule_eval.model_dump()
        )

