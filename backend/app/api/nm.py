"""
NM Physician API 路由
核醫醫師工作清單與案件操作
"""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    WorklistResponse,
    DraftRequest,
    DraftResponse,
    SubmitResponse,
    RespondRequest,
    RespondResponse,
)
from app.services.case_service import CaseService
from app.services.auth_service import get_current_user, CurrentUser

router = APIRouter()


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

