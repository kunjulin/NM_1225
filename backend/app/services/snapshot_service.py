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
        
        # 解析快照
        snapshot_data = json.loads(case.snapshot_json or "{}")
        snapshot = SnapshotData(
            conditions=snapshot_data.get("conditions", []),
            allergies=snapshot_data.get("allergies", []),
            observations=snapshot_data.get("observations", []),
            documents=snapshot_data.get("documents", []),
        )
        
        # 產生候選值
        candidate_facts = self._generate_candidate_facts(case, snapshot_data)
        
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
        """從 FHIR 重新擷取快照"""
        try:
            # 取得 Patient
            patient = await self.fhir_client.get_patient(case.patient_ref)
            
            # 取得最近的體重 Observation
            weight_obs = await self.fhir_client.get_latest_weight(case.patient_ref)
            
            # 取得過敏資料
            allergies = await self.fhir_client.get_allergies(case.patient_ref)
            
            # 組合快照
            snapshot = {
                "patientName": patient.get("name", [{}])[0].get("text", "Unknown"),
                "patientId": case.patient_ref,
                "observations": [weight_obs] if weight_obs else [],
                "allergies": allergies,
                "conditions": [],
                "documents": [],
            }
            
            if weight_obs:
                snapshot["weightKg"] = weight_obs.get("valueQuantity", {}).get("value")
            
            snapshot["hasAllergy"] = len(allergies) > 0
            
            case.snapshot_json = json.dumps(snapshot)
            case.updated_at = datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            # 擷取失敗時保留舊快照
            pass
    
    def _generate_candidate_facts(
        self, 
        case: OrderCase, 
        snapshot_data: dict
    ) -> list[CandidateFact]:
        """根據快照產生自動填入候選值"""
        candidates = []
        local_facts = json.loads(case.local_facts_json or "{}")
        
        # 體重候選值
        if "weightKg" not in local_facts:
            observations = snapshot_data.get("observations", [])
            for obs in observations:
                if obs.get("code", {}).get("coding", [{}])[0].get("code") == "29463-7":
                    value = obs.get("valueQuantity", {}).get("value")
                    if value:
                        candidates.append(CandidateFact(
                            factType=FactType.WEIGHT_KG,
                            value=float(value),
                            unit="kg",
                            asOf=datetime.fromisoformat(
                                obs.get("effectiveDateTime", datetime.now(timezone.utc).isoformat())
                            ),
                            sourceType=SourceType.FHIR_RESOURCE,
                            sourceRef=f"Observation/{obs.get('id', 'unknown')}",
                            confidence=Confidence.HIGH,
                            extractionMethod=ExtractionMethod.STRUCTURED,
                        ))
        
        return candidates
    
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
        
        await self.db.commit()
        
        # 重新評估規則
        rule_eval = self.rule_engine.evaluate(case)
        
        return ManualFactResponse(
            caseId=case_id,
            updatedLocalFacts=local_facts,
            cds=rule_eval.model_dump()
        )

