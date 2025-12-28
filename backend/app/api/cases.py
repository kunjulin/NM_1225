"""
Cases API 路由
病人快照與 Auto-fill 功能
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    PatientSnapshotResponse,
    AcceptAutoFillRequest,
    AcceptAutoFillResponse,
    RejectAutoFillRequest,
    RejectAutoFillResponse,
    ManualFactRequest,
    ManualFactResponse,
)
from app.services.snapshot_service import SnapshotService
from app.services.auth_service import get_current_user, CurrentUser

router = APIRouter()


@router.get("/{case_id}/snapshot", response_model=PatientSnapshotResponse)
async def get_snapshot(
    case_id: str,
    refresh: bool = Query(False, description="是否重新從 HIS FHIR 擷取"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得病人快照與自動填入候選值"""
    service = SnapshotService(db)
    return await service.get_snapshot(case_id, refresh=refresh)


@router.post("/{case_id}/autofill/accept", response_model=AcceptAutoFillResponse)
async def accept_autofill(
    case_id: str,
    request: AcceptAutoFillRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """接受自動填入候選值
    
    將候選值寫入 local_facts_json 並重新執行 CDS
    """
    service = SnapshotService(db)
    return await service.accept_autofill(case_id, request, current_user)


@router.post("/{case_id}/autofill/reject", response_model=RejectAutoFillResponse)
async def reject_autofill(
    case_id: str,
    request: RejectAutoFillRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """拒絕自動填入候選值（記錄稽核）"""
    service = SnapshotService(db)
    return await service.reject_autofill(case_id, request, current_user)


@router.post("/{case_id}/manual-fact", response_model=ManualFactResponse)
async def save_manual_fact(
    case_id: str,
    request: ManualFactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """手動輸入臨床資料
    
    允許醫師手動輸入缺少的臨床資料（如體重、eGFR）
    """
    service = SnapshotService(db)
    return await service.save_manual_fact(case_id, request, current_user)


@router.post("/{case_id}/refresh-clinical-data")
async def refresh_clinical_data(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """手動觸發臨床資料重新整理
    
    從 FHIR Server 重新拉取完整的臨床資料（Encounters, Conditions, Medications, Procedures, Lab Results, Allergies）
    並更新案件快照
    """
    from fastapi import HTTPException, status
    
    service = SnapshotService(db)
    try:
        # 使用 refresh=True 來觸發重新整理
        result = await service.get_snapshot(case_id, refresh=True)
        return {
            "success": True,
            "message": "臨床資料已重新整理",
            "caseId": case_id
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to refresh clinical data for case {case_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新整理臨床資料失敗: {str(e)}"
        )

