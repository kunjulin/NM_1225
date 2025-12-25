"""
案件服務
處理 OrderCase 的 CRUD 與工作流程操作
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OrderCase, ReviewEvent, Outbox
from app.schemas import (
    CaseStatus,
    WorklistResponse,
    WorklistGroup,
    WorklistItem,
    SnapshotSummary,
    DraftData,
    DraftResponse,
    SubmitResponse,
    ClaimResponse,
    ApproveResponse,
    ReturnRequest,
    ReturnResponse,
    RespondRequest,
    RespondResponse,
    BulkApproveResponse,
    BulkApproveResult,
    BulkSubmitResponse,
    BulkSubmitResult,
)
from app.schemas.rule_eval import RuleEval, Severity
from app.services.auth_service import CurrentUser
from app.rules.engine import RuleEngine


class CaseService:
    """案件服務"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rule_engine = RuleEngine()
    
    async def get_nm_worklist(
        self, 
        subject: str, 
        status_filter: Optional[str] = None
    ) -> WorklistResponse:
        """取得核醫工作清單"""
        # 定義核醫相關的狀態
        nm_statuses = [
            CaseStatus.NM_PENDING,
            CaseStatus.NM_DRAFTED,
            CaseStatus.RETURNED,
            CaseStatus.PHARM_READY,  # 唯讀顯示
        ]
        
        if status_filter:
            try:
                filter_status = CaseStatus(status_filter)
                if filter_status in nm_statuses:
                    nm_statuses = [filter_status]
            except ValueError:
                pass
        
        # 查詢案件
        query = select(OrderCase).where(
            OrderCase.status.in_([s.value for s in nm_statuses])
        ).order_by(OrderCase.updated_at.desc())
        
        result = await self.db.execute(query)
        cases = result.scalars().all()
        
        # 分群
        groups = {
            "NM_PENDING": WorklistGroup(
                groupKey="NM_PENDING",
                title="待核醫處理",
                count=0,
                items=[]
            ),
            "NM_DRAFTED": WorklistGroup(
                groupKey="NM_DRAFTED",
                title="已建立草案",
                count=0,
                items=[]
            ),
            "RETURNED": WorklistGroup(
                groupKey="RETURNED",
                title="藥師退回待回應",
                count=0,
                items=[]
            ),
            "PHARM_READY": WorklistGroup(
                groupKey="PHARM_READY",
                title="已送審（唯讀）",
                count=0,
                items=[]
            ),
        }
        
        for case in cases:
            try:
                item = self._case_to_worklist_item(case)
                
                # CDS FAIL 分群邏輯調整：
                # NM_DRAFTED 狀態但 CDS 評估為 FAIL 的案件，移至「待核醫處理」群組
                # 這樣醫師必須先處理問題後才能在「已建立草案」Tab 批次送審
                target_group = case.status
                
                if case.status == CaseStatus.NM_DRAFTED.value:
                    if item.ruleEval.overallSeverity == Severity.FAIL:
                        # CDS FAIL 的草案需要回到待處理狀態
                        target_group = CaseStatus.NM_PENDING.value
                
                if target_group in groups:
                    groups[target_group].items.append(item)
                    groups[target_group].count += 1
            except Exception as e:
                import logging
                logging.error(f"Error processing case {case.id}: {e}", exc_info=True)
                # 跳過有問題的案件，繼續處理其他案件
                continue
        
        return WorklistResponse(
            groups=[g for g in groups.values() if g.count > 0]
        )
    
    async def get_pharmacy_worklist(
        self, 
        subject: str, 
        status_filter: Optional[str] = None
    ) -> WorklistResponse:
        """取得藥師工作清單"""
        # 查詢待審、進行中與已批准的案件
        query = select(OrderCase).where(
            OrderCase.status.in_([
                CaseStatus.PHARM_READY.value,
                CaseStatus.PHARM_IN_PROGRESS.value,
                CaseStatus.APPROVED.value,
            ])
        ).order_by(OrderCase.updated_at.desc())
        
        result = await self.db.execute(query)
        cases = result.scalars().all()
        
        # 分群
        exceptions = []
        batch_eligible = []
        my_claimed = []
        approved = []
        
        for case in cases:
            item = self._case_to_worklist_item(case)
            
            # 已批准的案件分到 approved 群組
            if case.status == CaseStatus.APPROVED.value:
                approved.append(item)
            elif case.owner_subject == subject:
                my_claimed.append(item)
            elif not item.ruleEval.isBatchEligible or item.ruleEval.overallSeverity == Severity.FAIL:
                exceptions.append(item)
            else:
                batch_eligible.append(item)
        
        return WorklistResponse(
            groups=[
                WorklistGroup(
                    groupKey="exceptions",
                    title="需逐筆審查",
                    count=len(exceptions),
                    items=exceptions
                ),
                WorklistGroup(
                    groupKey="batchEligible",
                    title="可批次核准",
                    count=len(batch_eligible),
                    items=batch_eligible
                ),
                WorklistGroup(
                    groupKey="approved",
                    title="已批准",
                    count=len(approved),
                    items=approved
                ),
                WorklistGroup(
                    groupKey="myClaimed",
                    title="我已 Claim",
                    count=len(my_claimed),
                    items=my_claimed
                ),
            ]
        )
    
    async def save_draft(
        self, 
        case_id: str, 
        draft: DraftData, 
        current_user: CurrentUser
    ) -> DraftResponse:
        """儲存用藥草案"""
        case = await self._get_case(case_id)
        
        # 驗證狀態
        if case.status not in [CaseStatus.NM_PENDING.value, CaseStatus.NM_DRAFTED.value, CaseStatus.RETURNED.value]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot save draft in status: {case.status}"
            )
        
        # 更新草案
        case.draft_json = json.dumps(draft.model_dump())
        case.status = CaseStatus.NM_DRAFTED.value
        case.updated_at = datetime.now(timezone.utc).isoformat()
        
        # 執行規則引擎
        rule_eval = self.rule_engine.evaluate(case)
        
        await self.db.commit()
        
        return DraftResponse(
            caseId=case_id,
            status=CaseStatus(case.status),
            draft=draft,
            ruleEval=rule_eval
        )
    
    async def submit_to_pharmacy(
        self, 
        case_id: str, 
        current_user: CurrentUser
    ) -> SubmitResponse:
        """送交藥師審查"""
        case = await self._get_case(case_id)
        
        # 驗證狀態
        if case.status != CaseStatus.NM_DRAFTED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot submit from status: {case.status}"
            )
        
        # 更新狀態
        case.status = CaseStatus.PHARM_READY.value
        case.updated_at = datetime.now(timezone.utc).isoformat()
        
        # 建立審查事件
        event = ReviewEvent(
            id=str(uuid.uuid4()),
            case_id=case_id,
            event_type="SUBMIT",
            actor_subject=current_user.subject,
            acting_role=current_user.acting_role.value,
            payload_json=json.dumps({"action": "submit_to_pharmacy"}),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(event)
        
        await self.db.commit()
        
        return SubmitResponse(
            caseId=case_id,
            status=CaseStatus.PHARM_READY
        )
    
    async def claim_case(
        self, 
        case_id: str, 
        current_user: CurrentUser
    ) -> ClaimResponse:
        """Claim 案件"""
        case = await self._get_case(case_id)
        
        # 驗證狀態
        if case.status != CaseStatus.PHARM_READY.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot claim case in status: {case.status}"
            )
        
        # 原子性更新
        case.status = CaseStatus.PHARM_IN_PROGRESS.value
        case.owner_subject = current_user.subject
        case.updated_at = datetime.now(timezone.utc).isoformat()
        
        # 建立事件
        event = ReviewEvent(
            id=str(uuid.uuid4()),
            case_id=case_id,
            event_type="CLAIM",
            actor_subject=current_user.subject,
            acting_role=current_user.acting_role.value,
            payload_json=json.dumps({"action": "claim"}),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(event)
        
        await self.db.commit()
        
        return ClaimResponse(
            caseId=case_id,
            status=CaseStatus.PHARM_IN_PROGRESS,
            ownerSubject=current_user.subject
        )
    
    async def approve_case(
        self, 
        case_id: str, 
        current_user: CurrentUser
    ) -> ApproveResponse:
        """核准案件"""
        case = await self._get_case(case_id)
        
        # 驗證狀態與權限
        if case.status == CaseStatus.PHARM_READY.value:
            # 自動 claim
            case.owner_subject = current_user.subject
        elif case.status != CaseStatus.PHARM_IN_PROGRESS.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot approve case in status: {case.status}"
            )
        elif case.owner_subject != current_user.subject:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner can approve this case"
            )
        
        # 更新狀態
        case.status = CaseStatus.APPROVED.value
        case.updated_at = datetime.now(timezone.utc).isoformat()
        
        # 建立事件
        event = ReviewEvent(
            id=str(uuid.uuid4()),
            case_id=case_id,
            event_type="APPROVE",
            actor_subject=current_user.subject,
            acting_role=current_user.acting_role.value,
            payload_json=json.dumps({"action": "approve"}),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(event)
        
        # 加入 Outbox 進行延遲 write-back
        outbox = Outbox(
            id=str(uuid.uuid4()),
            case_id=case_id,
            operation="CREATE_MEDICATION_REQUEST",
            request_json=case.draft_json or "{}",
            status="PENDING",
            retry_count=0,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(outbox)
        
        await self.db.commit()
        
        return ApproveResponse(
            caseId=case_id,
            status=CaseStatus.APPROVED
        )
    
    async def return_case(
        self, 
        case_id: str, 
        request: ReturnRequest,
        current_user: CurrentUser
    ) -> ReturnResponse:
        """退回案件給核醫"""
        case = await self._get_case(case_id)
        
        # 驗證狀態
        if case.status not in [CaseStatus.PHARM_READY.value, CaseStatus.PHARM_IN_PROGRESS.value]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot return case in status: {case.status}"
            )
        
        # 更新狀態
        case.status = CaseStatus.RETURNED.value
        case.owner_subject = None
        case.updated_at = datetime.now(timezone.utc).isoformat()
        
        # 建立事件
        event = ReviewEvent(
            id=str(uuid.uuid4()),
            case_id=case_id,
            event_type="RETURN",
            actor_subject=current_user.subject,
            acting_role=current_user.acting_role.value,
            payload_json=json.dumps({
                "returnReasonCodes": [r.value for r in request.returnReasonCodes],
                "comment": request.comment
            }),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self.db.add(event)
        
        await self.db.commit()
        
        return ReturnResponse(
            caseId=case_id,
            status=CaseStatus.RETURNED
        )
    
    async def respond_to_return(
        self, 
        case_id: str, 
        request: RespondRequest,
        current_user: CurrentUser
    ) -> RespondResponse:
        """回應藥師退回並重新送審
        
        回應後自動將案件送交藥師審查（狀態改為 PHARM_READY）
        """
        case = await self._get_case(case_id)
        
        # 驗證狀態
        if case.status != CaseStatus.RETURNED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot respond in status: {case.status}"
            )
        
        # 更新草案（如有）
        if request.updatedDraft:
            case.draft_json = json.dumps(request.updatedDraft.model_dump())
        
        # 回應後直接送審（狀態改為 PHARM_READY，而不是 NM_DRAFTED）
        case.status = CaseStatus.PHARM_READY.value
        case.updated_at = datetime.now(timezone.utc).isoformat()
        
        now = datetime.now(timezone.utc).isoformat()
        
        # 建立回應事件
        response_event = ReviewEvent(
            id=str(uuid.uuid4()),
            case_id=case_id,
            event_type="RESPONSE",
            actor_subject=current_user.subject,
            acting_role=current_user.acting_role.value,
            payload_json=json.dumps({
                "responseAction": request.responseAction.value,
                "comment": request.comment
            }),
            created_at=now
        )
        self.db.add(response_event)
        
        # 建立送審事件
        submit_event = ReviewEvent(
            id=str(uuid.uuid4()),
            case_id=case_id,
            event_type="SUBMIT",
            actor_subject=current_user.subject,
            acting_role=current_user.acting_role.value,
            payload_json=json.dumps({"action": "resubmit_after_response"}),
            created_at=now
        )
        self.db.add(submit_event)
        
        await self.db.commit()
        
        return RespondResponse(
            caseId=case_id,
            status=CaseStatus.PHARM_READY
        )
    
    async def bulk_approve(
        self, 
        case_ids: list[str], 
        note: Optional[str],
        current_user: CurrentUser
    ) -> BulkApproveResponse:
        """批次核准"""
        ok_results = []
        failed_results = []
        
        for case_id in case_ids:
            try:
                case = await self._get_case(case_id)
                
                # 檢查批次核准資格
                rule_eval = self.rule_engine.evaluate(case)
                if not rule_eval.isBatchEligible:
                    failed_results.append(BulkApproveResult(
                        caseId=case_id,
                        code="NOT_BATCH_ELIGIBLE",
                        message="Case is not eligible for batch approval"
                    ))
                    continue
                
                if rule_eval.overallSeverity == Severity.FAIL:
                    failed_results.append(BulkApproveResult(
                        caseId=case_id,
                        code="HAS_FAIL_FLAGS",
                        message="Case has FAIL severity flags"
                    ))
                    continue
                
                # 執行核准
                result = await self.approve_case(case_id, current_user)
                ok_results.append(BulkApproveResult(
                    caseId=case_id,
                    status=result.status
                ))
                
            except HTTPException as e:
                failed_results.append(BulkApproveResult(
                    caseId=case_id,
                    code="ERROR",
                    message=str(e.detail)
                ))
        
        return BulkApproveResponse(ok=ok_results, failed=failed_results)
    
    async def bulk_submit(
        self, 
        case_ids: list[str], 
        note: Optional[str],
        current_user: CurrentUser
    ) -> BulkSubmitResponse:
        """批次送審 (NM 批次送交藥師審查)
        
        僅處理 NM_DRAFTED 狀態且 CDS 非 FAIL 的案件。
        CDS 為 FAIL 的案件需個別處理後才能送審。
        """
        ok_results = []
        failed_results = []
        
        for case_id in case_ids:
            try:
                case = await self._get_case(case_id)
                
                # 檢查狀態
                if case.status != CaseStatus.NM_DRAFTED.value:
                    failed_results.append(BulkSubmitResult(
                        caseId=case_id,
                        code="INVALID_STATUS",
                        message=f"案件狀態不正確: {case.status}，需為 NM_DRAFTED"
                    ))
                    continue
                
                # 檢查 CDS 評估結果
                rule_eval = self.rule_engine.evaluate(case)
                
                # 檢查是否有 Override 理由
                draft = json.loads(case.draft_json or "{}")
                override = draft.get("override") or {}
                has_override_reason = override.get("isOverride") and override.get("reason")
                
                # 如果 CDS FAIL 且沒有 Override 理由，則不能送審
                if rule_eval.overallSeverity == Severity.FAIL and not has_override_reason:
                    fail_flags = [f.title for f in rule_eval.flags if f.severity == Severity.FAIL]
                    failed_results.append(BulkSubmitResult(
                        caseId=case_id,
                        code="CDS_FAIL",
                        message=f"CDS 評估失敗，需處理問題或提供 Override 理由後才能送審: {', '.join(fail_flags)}"
                    ))
                    continue
                
                # 執行送審
                result = await self.submit_to_pharmacy(case_id, current_user)
                ok_results.append(BulkSubmitResult(
                    caseId=case_id,
                    status=result.status
                ))
                
            except HTTPException as e:
                failed_results.append(BulkSubmitResult(
                    caseId=case_id,
                    code="ERROR",
                    message=str(e.detail)
                ))
            except Exception as e:
                # 捕捉所有其他異常，避免整個批次失敗
                import logging
                logging.error(f"Error in bulk_submit for case {case_id}: {e}", exc_info=True)
                failed_results.append(BulkSubmitResult(
                    caseId=case_id,
                    code="ERROR",
                    message=f"處理案件時發生錯誤: {str(e)}"
                ))
        
        return BulkSubmitResponse(ok=ok_results, failed=failed_results)
    
    async def _get_case(self, case_id: str) -> OrderCase:
        """取得案件（含錯誤處理）"""
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
    
    def _case_to_worklist_item(self, case: OrderCase) -> WorklistItem:
        """轉換 OrderCase 為 WorklistItem"""
        try:
            # 解析 snapshot 和 local_facts
            snapshot_data = json.loads(case.snapshot_json or "{}")
            local_facts = json.loads(case.local_facts_json or "{}")
            
            # 優先使用 local_facts 中的體重（手動輸入或自動填入）
            weight_kg = local_facts.get("weightKg", {}).get("value") if isinstance(local_facts.get("weightKg"), dict) else None
            if not weight_kg:
                weight_kg = snapshot_data.get("weightKg")
            
            snapshot_summary = SnapshotSummary(
                patientName=snapshot_data.get("patientName"),
                patientId=snapshot_data.get("patientId"),
                examCode=snapshot_data.get("examCode"),
                examDisplay=snapshot_data.get("examDisplay"),
                weightKg=weight_kg,
                hasAllergy=snapshot_data.get("hasAllergy"),
            )
            
            # 執行規則引擎
            rule_eval = self.rule_engine.evaluate(case)
            
            # 安全解析時間
            try:
                created_at = datetime.fromisoformat(case.created_at.replace('Z', '+00:00'))
            except:
                created_at = datetime.now(timezone.utc)
            
            try:
                updated_at = datetime.fromisoformat(case.updated_at.replace('Z', '+00:00'))
            except:
                updated_at = datetime.now(timezone.utc)
            
            return WorklistItem(
                caseId=case.id,
                patientRef=case.patient_ref,
                serviceRequestRef=case.service_request_ref,
                status=CaseStatus(case.status),
                ownerSubject=case.owner_subject,
                snapshotSummary=snapshot_summary,
                ruleEval=rule_eval,
                createdAt=created_at,
                updatedAt=updated_at,
            )
        except Exception as e:
            # 如果轉換失敗，返回一個基本的 WorklistItem
            import logging
            logging.error(f"Error converting case {case.id} to worklist item: {e}")
            
            return WorklistItem(
                caseId=case.id,
                patientRef=case.patient_ref,
                serviceRequestRef=case.service_request_ref,
                status=CaseStatus(case.status),
                ownerSubject=case.owner_subject,
                snapshotSummary=SnapshotSummary(),
                ruleEval=RuleEval.passing(),
                createdAt=datetime.now(timezone.utc),
                updatedAt=datetime.now(timezone.utc),
            )

