"""
Analytics API 路由
KPI 與統計分析、CSV 匯出、同步記錄
"""
import csv
import io
import json
from datetime import date, datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.schemas import AnalyticsSummary, AutofillSummary
from app.schemas.case import CaseStatus
from app.models import OrderCase, ReviewEvent, Outbox, User
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import get_current_user, CurrentUser
from app.services.outbox_worker import OutboxWorker
from fastapi import HTTPException, status

router = APIRouter()


# === Sync Log Schemas ===

class SyncLogItem(BaseModel):
    """同步記錄項目"""
    id: str
    case_id: str
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    operation: str
    status: str
    medication_request_ref: Optional[str] = None
    last_error: Optional[str] = None
    retry_count: int
    created_at: str
    updated_at: str


class SyncLogResponse(BaseModel):
    """同步記錄回應"""
    logs: List[SyncLogItem]
    total: int
    page: int
    page_size: int


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    from_date: date = Query(..., alias="from", description="起始日期"),
    to_date: date = Query(..., alias="to", description="結束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得 KPI 摘要
    
    包含：
    - 不適當劑量比例
    - 藥師介入率
    - 處理時間統計
    - 退回原因分佈
    """
    service = AnalyticsService(db)
    return await service.get_summary(from_date, to_date)


@router.get("/autofill/summary", response_model=AutofillSummary)
async def get_autofill_summary(
    from_date: date = Query(..., alias="from", description="起始日期"),
    to_date: date = Query(..., alias="to", description="結束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得 Auto-fill 統計摘要"""
    service = AnalyticsService(db)
    return await service.get_autofill_summary(from_date, to_date)


@router.get("/export/csv")
async def export_cases_csv(
    from_date: date = Query(..., alias="from", description="起始日期"),
    to_date: date = Query(..., alias="to", description="結束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """匯出已審查完成的藥單清單為 CSV
    
    只匯出 APPROVED、SYNCED 狀態的案件
    
    CSV 欄位：
    - 病患姓名
    - 病患ID
    - 檢查名稱
    - 劑量
    - 建立醫師
    - 審查藥師
    - 批准日期
    """
    # 查詢已審查完成的案件
    from_str = from_date.isoformat()
    to_str = (date(to_date.year, to_date.month, to_date.day)).isoformat() + "T23:59:59"
    
    # 查詢 APPROVED 或 SYNCED 狀態的案件
    result = await db.execute(
        select(OrderCase).where(
            and_(
                OrderCase.status.in_([CaseStatus.APPROVED.value, CaseStatus.SYNCED.value]),
                OrderCase.updated_at >= from_str,
                OrderCase.updated_at <= to_str,
            )
        ).order_by(OrderCase.updated_at.desc())
    )
    cases = result.scalars().all()
    
    # 收集所有案件 ID 以查詢審查事件
    case_ids = [c.id for c in cases]
    
    # 查詢相關的審查事件
    events_result = await db.execute(
        select(ReviewEvent).where(
            and_(
                ReviewEvent.case_id.in_(case_ids),
                ReviewEvent.event_type.in_(["SUBMIT", "APPROVE"])
            )
        )
    )
    events = events_result.scalars().all()
    
    # 建立事件索引
    submit_events = {}  # case_id -> actor_subject
    approve_events = {}  # case_id -> (actor_subject, created_at)
    
    for event in events:
        if event.event_type == "SUBMIT":
            submit_events[event.case_id] = event.actor_subject
        elif event.event_type == "APPROVE":
            approve_events[event.case_id] = (event.actor_subject, event.created_at)
    
    # 收集所有 actor_subject 以查詢使用者名稱
    all_subjects = set()
    for subject in submit_events.values():
        if subject:
            all_subjects.add(subject)
    for subject, _ in approve_events.values():
        if subject:
            all_subjects.add(subject)
    
    # 查詢使用者資訊
    user_map = {}  # subject -> display_name
    if all_subjects:
        users_result = await db.execute(
            select(User).where(User.subject.in_(list(all_subjects)))
        )
        users = users_result.scalars().all()
        for user in users:
            user_map[user.subject] = user.display_name
    
    # 建立 CSV 內容（使用 StringIO）
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 標題列
    writer.writerow([
        "病患姓名",
        "病患ID", 
        "檢查名稱",
        "使用時間",
        "劑量",
        "建立醫師",
        "審查藥師",
        "批准日期",
    ])
    
    # 資料列
    for case in cases:
        snapshot = json.loads(case.snapshot_json or "{}")
        draft = json.loads(case.draft_json or "{}")
        
        # 取得劑量資訊
        dose = draft.get("suggestedDose", {})
        dose_str = ""
        if dose:
            dose_value = dose.get("value", "")
            dose_unit = dose.get("unit", "MBq")
            dose_str = f"{dose_value} {dose_unit}" if dose_value else ""
        
        # 取得使用時間（occurrenceDateTime）
        occurrence_datetime = snapshot.get("occurrenceDateTime", "")
        occurrence_str = ""
        if occurrence_datetime:
            try:
                dt = datetime.fromisoformat(occurrence_datetime.replace('Z', '+00:00'))
                occurrence_str = dt.strftime("%Y/%m/%d %H:%M")
            except:
                occurrence_str = occurrence_datetime
        
        # 取得審查資訊
        submit_subject = submit_events.get(case.id, "")
        approve_info = approve_events.get(case.id, ("", ""))
        approve_subject = approve_info[0]
        approve_date = approve_info[1]
        
        # 將 subject 轉換為 display_name
        submit_actor_name = user_map.get(submit_subject, submit_subject) if submit_subject else ""
        approve_actor_name = user_map.get(approve_subject, approve_subject) if approve_subject else ""
        
        # 格式化日期
        if approve_date:
            try:
                dt = datetime.fromisoformat(approve_date.replace('Z', '+00:00'))
                approve_date = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
        writer.writerow([
            snapshot.get("patientName", ""),
            snapshot.get("patientId", ""),
            snapshot.get("examDisplay", ""),
            occurrence_str,
            dose_str,
            submit_actor_name,
            approve_actor_name,
            approve_date,
        ])
    
    # 取得 CSV 文字並加上 BOM
    csv_text = output.getvalue()
    output.close()
    
    # 手動組合 BOM + UTF-8 編碼的內容
    bom = b'\xef\xbb\xbf'
    csv_bytes = bom + csv_text.encode('utf-8')
    
    filename = f"medication_orders_{from_date.isoformat()}_{to_date.isoformat()}.csv"
    
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
        }
    )


@router.get("/sync-logs", response_model=SyncLogResponse)
async def get_sync_logs(
    from_date: date = Query(..., alias="from", description="起始日期"),
    to_date: date = Query(..., alias="to", description="結束日期"),
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁筆數"),
    status_filter: Optional[str] = Query(None, alias="status", description="狀態過濾"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得 FHIR 同步記錄
    
    顯示 MedicationRequest 上傳到 FHIR Server 的記錄
    """
    from_str = from_date.isoformat()
    to_str = (date(to_date.year, to_date.month, to_date.day)).isoformat() + "T23:59:59"
    
    # 建構查詢
    query = select(Outbox).where(
        and_(
            Outbox.created_at >= from_str,
            Outbox.created_at <= to_str,
        )
    )
    
    if status_filter:
        query = query.where(Outbox.status == status_filter)
    
    query = query.order_by(Outbox.created_at.desc())
    
    # 計算總數
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())
    
    # 分頁
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    outbox_items = result.scalars().all()
    
    # 收集案件 ID 以取得病患資訊
    case_ids = [item.case_id for item in outbox_items]
    
    cases_result = await db.execute(
        select(OrderCase).where(OrderCase.id.in_(case_ids))
    )
    cases = {c.id: c for c in cases_result.scalars().all()}
    
    # 建構回應
    logs = []
    for item in outbox_items:
        case = cases.get(item.case_id)
        snapshot = json.loads(case.snapshot_json or "{}") if case else {}
        
        logs.append(SyncLogItem(
            id=item.id,
            case_id=item.case_id,
            patient_name=snapshot.get("patientName"),
            patient_id=snapshot.get("patientId"),
            operation=item.operation,
            status=item.status,
            medication_request_ref=case.final_fhir_medication_request_ref if case else None,
            last_error=item.last_error,
            retry_count=item.retry_count,
            created_at=item.created_at,
            updated_at=item.updated_at,
        ))
    
    return SyncLogResponse(
        logs=logs,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/sync-logs/{outbox_id}/retry")
async def retry_sync_log(
    outbox_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """手動重試失敗的 FHIR 同步記錄
    
    允許管理員或藥師手動觸發失敗的 MedicationRequest 上傳重試
    """
    # 查詢 Outbox 項目
    result = await db.execute(
        select(Outbox).where(Outbox.id == outbox_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Outbox item {outbox_id} not found"
        )
    
    # 只有 FAILED 或 PENDING 狀態的項目可以手動重試
    if item.status not in ["FAILED", "PENDING"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot retry outbox item in status: {item.status}. Only FAILED or PENDING items can be retried."
        )
    
    # 使用 OutboxWorker 重試
    worker = OutboxWorker()
    
    try:
        # 重置狀態為 PENDING，清除 next_retry_at，立即處理
        item.status = "PENDING"
        item.next_retry_at = None
        item.updated_at = datetime.now(timezone.utc).isoformat()
        
        # 立即處理
        await worker._process_item(db, item)
        
        await db.commit()
        
        # 查詢更新後的狀態
        await db.refresh(item)
        
        return {
            "success": item.status == "DONE",
            "status": item.status,
            "last_error": item.last_error,
            "retry_count": item.retry_count,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry: {str(e)}"
        )


