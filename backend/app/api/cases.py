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

