"""
NM Physician API 路由
核醫醫師工作清單與案件操作
"""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.schemas import (
    WorklistResponse,
    DraftRequest,
    DraftResponse,
    SubmitResponse,
    RespondRequest,
    RespondResponse,
    BulkSubmitRequest,
    BulkSubmitResponse,
)
from app.services.case_service import CaseService
from app.services.fhir_sync_service import FHIRSyncService
from app.services.auth_service import get_current_user, CurrentUser
from app.services.outbox_worker import get_sync_status

router = APIRouter()


# === Sync Schemas ===

class SyncWorklistResponse(BaseModel):
    """同步工作清單回應"""
    fetched: int
    created: int
    skipped: int
    errors: int
    error_details: list[str] = []


class SyncStatusResponse(BaseModel):
    """同步狀態回應"""
    lastSyncTime: Optional[str] = None
    nextSyncIn: Optional[int] = None
    isWorkerRunning: bool = False
    syncIntervalSeconds: float = 60.0


@router.get("/worklist", response_model=WorklistResponse)
async def get_nm_worklist(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得核醫工作清單
    
    分群顯示：
    - NM_PENDING: 待核醫處理
    - NM_DRAFTED: 已建立草案
    - RETURNED: 藥師退回待回應
    """
    try:
        service = CaseService(db)
        result = await service.get_nm_worklist(current_user.subject, status)
        return result
    except Exception as e:
        import logging
        logging.error(f"Error getting NM worklist: {e}", exc_info=True)
        # 返回空的工作清單而不是錯誤
        from app.schemas import WorklistResponse, WorklistGroup
        return WorklistResponse(groups=[])


@router.post("/cases/{case_id}/draft", response_model=DraftResponse)
async def save_draft(
    case_id: str,
    request: DraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """建立或更新用藥草案"""
    service = CaseService(db)
    return await service.save_draft(case_id, request.draft, current_user)


@router.post("/cases/{case_id}/submit", response_model=SubmitResponse)
async def submit_to_pharmacy(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """送交藥師審查"""
    service = CaseService(db)
    return await service.submit_to_pharmacy(case_id, current_user)


@router.post("/cases/{case_id}/respond", response_model=RespondResponse)
async def respond_to_return(
    case_id: str,
    request: RespondRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """回應藥師退回"""
    service = CaseService(db)
    return await service.respond_to_return(case_id, request, current_user)


@router.post("/bulk-submit", response_model=BulkSubmitResponse)
async def bulk_submit(
    request: BulkSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """批次送交藥師審查
    
    將多個 NM_DRAFTED 狀態且 CDS 非 FAIL 的案件批次送審。
    CDS 為 FAIL 的案件將被排除，需個別處理。
    
    Args:
        request: 包含要送審的案件 ID 列表
        
    Returns:
        成功與失敗的案件列表
    """
    try:
        service = CaseService(db)
        return await service.bulk_submit(request.caseIds, request.note, current_user)
    except Exception as e:
        import logging
        logging.error(f"Error in bulk_submit API: {e}", exc_info=True)
        # 重新拋出為 HTTPException，讓 FastAPI 處理
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批次送審時發生系統錯誤: {str(e)}"
        )


@router.get("/sync-status", response_model=SyncStatusResponse)
async def get_sync_status_api(
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得 FHIR 同步狀態
    
    Returns:
        同步狀態資訊（最後同步時間、下次同步倒數、Worker 狀態等）
    """
    status = get_sync_status()
    return SyncStatusResponse(
        lastSyncTime=status.get("last_sync_time"),
        nextSyncIn=status.get("next_sync_in"),
        isWorkerRunning=status.get("is_running", False),
        syncIntervalSeconds=status.get("sync_interval_seconds", 60.0),
    )


@router.post("/sync-worklist", response_model=SyncWorklistResponse)
async def sync_worklist_from_fhir(
    last_updated: Optional[str] = Query(None, description="只同步此時間之後更新的 ServiceRequest"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """從 FHIR Server 同步 ServiceRequest 到工作清單
    
    手動觸發從 THAS/FHIR Server 拉取核醫相關的 ServiceRequest，
    並建立對應的 OrderCase 到本地工作清單。
    
    Args:
        last_updated: 可選，只同步指定時間之後更新的資料
        
    Returns:
        同步統計結果
    """
    try:
        sync_service = FHIRSyncService(db)
        result = await sync_service.sync_service_requests(last_updated=last_updated)
        
        return SyncWorklistResponse(
            fetched=result["fetched"],
            created=result["created"],
            skipped=result["skipped"],
            errors=result["errors"],
            error_details=result.get("error_details", []),
        )
    except Exception as e:
        import logging
        logging.error(f"Error syncing worklist: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步工作清單時發生錯誤: {str(e)}"
        )

