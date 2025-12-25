"""
Analytics 服務
KPI 計算與統計分析
"""
import json
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OrderCase, ReviewEvent
from app.schemas import (
    AnalyticsSummary,
    AutofillSummary,
    DateWindow,
    TATStats,
    ReturnReasonStat,
    ResponseActionStat,
    FactTypeStat,
    AutofillImpact,
    CaseStatus,
)


class AnalyticsService:
    """Analytics 服務"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_summary(
        self, 
        from_date: date, 
        to_date: date
    ) -> AnalyticsSummary:
        """取得 KPI 摘要"""
        window = DateWindow(from_date=from_date, to_date=to_date)
        
        # 查詢期間內的案件
        from_dt = datetime.combine(from_date, datetime.min.time()).isoformat()
        to_dt = datetime.combine(to_date, datetime.max.time()).isoformat()
        
        # 總案件數
        total_query = select(func.count(OrderCase.id)).where(
            and_(
                OrderCase.created_at >= from_dt,
                OrderCase.created_at <= to_dt
            )
        )
        total_result = await self.db.execute(total_query)
        total_cases = total_result.scalar() or 0
        
        # 藥師介入事件 (RETURN + REJECT)
        intervention_query = select(func.count(ReviewEvent.id)).where(
            and_(
                ReviewEvent.created_at >= from_dt,
                ReviewEvent.created_at <= to_dt,
                ReviewEvent.event_type.in_(["RETURN", "REJECT"])
            )
        )
        intervention_result = await self.db.execute(intervention_query)
        intervention_count = intervention_result.scalar() or 0
        
        # 已送審案件數
        submitted_query = select(func.count(ReviewEvent.id)).where(
            and_(
                ReviewEvent.created_at >= from_dt,
                ReviewEvent.created_at <= to_dt,
                ReviewEvent.event_type == "SUBMIT"
            )
        )
        submitted_result = await self.db.execute(submitted_query)
        submitted_count = submitted_result.scalar() or 0
        
        pharmacist_intervention_rate = (
            intervention_count / submitted_count if submitted_count > 0 else 0.0
        )
        
        # 退回原因分佈
        return_events_query = select(ReviewEvent).where(
            and_(
                ReviewEvent.created_at >= from_dt,
                ReviewEvent.created_at <= to_dt,
                ReviewEvent.event_type == "RETURN"
            )
        )
        return_events_result = await self.db.execute(return_events_query)
        return_events = return_events_result.scalars().all()
        
        return_reasons_count = {}
        for event in return_events:
            payload = json.loads(event.payload_json or "{}")
            for code in payload.get("returnReasonCodes", []):
                return_reasons_count[code] = return_reasons_count.get(code, 0) + 1
        
        return_reasons = [
            ReturnReasonStat(
                code=code,
                count=count,
                rate=count / len(return_events) if return_events else 0.0
            )
            for code, count in return_reasons_count.items()
        ]
        
        # 回應動作分佈
        response_events_query = select(ReviewEvent).where(
            and_(
                ReviewEvent.created_at >= from_dt,
                ReviewEvent.created_at <= to_dt,
                ReviewEvent.event_type == "RESPONSE"
            )
        )
        response_events_result = await self.db.execute(response_events_query)
        response_events = response_events_result.scalars().all()
        
        response_actions_count = {}
        for event in response_events:
            payload = json.loads(event.payload_json or "{}")
            action = payload.get("responseAction", "UNKNOWN")
            response_actions_count[action] = response_actions_count.get(action, 0) + 1
        
        response_actions = [
            ResponseActionStat(
                action=action,
                count=count,
                rate=count / len(response_events) if response_events else 0.0
            )
            for action, count in response_actions_count.items()
        ]
        
        # 批次核准率（簡化計算）
        approved_query = select(func.count(OrderCase.id)).where(
            and_(
                OrderCase.updated_at >= from_dt,
                OrderCase.updated_at <= to_dt,
                OrderCase.status.in_([
                    CaseStatus.APPROVED.value,
                    CaseStatus.SYNCED.value,
                    CaseStatus.SYNCING.value
                ])
            )
        )
        approved_result = await self.db.execute(approved_query)
        approved_count = approved_result.scalar() or 0
        
        batch_approval_rate = approved_count / total_cases if total_cases > 0 else 0.0
        
        return AnalyticsSummary(
            window=window,
            totalCases=total_cases,
            inappropriateDoseRate=0.0,  # 需要更複雜的計算
            pharmacistInterventionRate=pharmacist_intervention_rate,
            medianTAT=0.0,  # 需要計算
            batchApprovalRate=batch_approval_rate,
            returnReasons=return_reasons,
            responseActions=response_actions,
            missingDataRate=0.0,
            overrideRate=0.0,
        )
    
    async def get_autofill_summary(
        self, 
        from_date: date, 
        to_date: date
    ) -> AutofillSummary:
        """取得 Auto-fill 統計摘要"""
        window = DateWindow(from_date=from_date, to_date=to_date)
        
        from_dt = datetime.combine(from_date, datetime.min.time()).isoformat()
        to_dt = datetime.combine(to_date, datetime.max.time()).isoformat()
        
        # 接受的 autofill 事件
        accept_query = select(ReviewEvent).where(
            and_(
                ReviewEvent.created_at >= from_dt,
                ReviewEvent.created_at <= to_dt,
                ReviewEvent.event_type == "AUTOFILL_ACCEPT"
            )
        )
        accept_result = await self.db.execute(accept_query)
        accept_events = accept_result.scalars().all()
        
        # 拒絕的 autofill 事件
        reject_query = select(ReviewEvent).where(
            and_(
                ReviewEvent.created_at >= from_dt,
                ReviewEvent.created_at <= to_dt,
                ReviewEvent.event_type == "AUTOFILL_REJECT"
            )
        )
        reject_result = await self.db.execute(reject_query)
        reject_events = reject_result.scalars().all()
        
        # 統計
        accepted_count = 0
        rejected_count = 0
        by_fact_type = {}
        
        for event in accept_events:
            payload = json.loads(event.payload_json or "{}")
            facts = payload.get("facts", [])
            accepted_count += len(facts)
            for fact in facts:
                ft = fact.get("factType", "UNKNOWN")
                if ft not in by_fact_type:
                    by_fact_type[ft] = {"generated": 0, "accepted": 0, "rejected": 0}
                by_fact_type[ft]["accepted"] += 1
                by_fact_type[ft]["generated"] += 1
        
        for event in reject_events:
            payload = json.loads(event.payload_json or "{}")
            rejections = payload.get("rejections", [])
            rejected_count += len(rejections)
            for rej in rejections:
                ft = rej.get("factType", "UNKNOWN")
                if ft not in by_fact_type:
                    by_fact_type[ft] = {"generated": 0, "accepted": 0, "rejected": 0}
                by_fact_type[ft]["rejected"] += 1
                by_fact_type[ft]["generated"] += 1
        
        total_generated = accepted_count + rejected_count
        accept_rate = accepted_count / total_generated if total_generated > 0 else 0.0
        
        fact_type_stats = [
            FactTypeStat(
                factType=ft,
                generated=data["generated"],
                accepted=data["accepted"],
                rejected=data["rejected"],
                acceptRate=data["accepted"] / data["generated"] if data["generated"] > 0 else 0.0
            )
            for ft, data in by_fact_type.items()
        ]
        
        return AutofillSummary(
            window=window,
            candidatesGenerated=total_generated,
            candidatesAccepted=accepted_count,
            candidatesRejected=rejected_count,
            acceptRate=accept_rate,
            byFactType=fact_type_stats,
        )

