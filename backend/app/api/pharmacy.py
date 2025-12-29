"""
Pharmacy API 路由
藥師工作清單與案件審核操作
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    WorklistResponse,
    ClaimResponse,
    ApproveResponse,
    ReturnRequest,
    ReturnResponse,
    BulkApproveRequest,
    BulkApproveResponse,
)
from app.services.case_service import CaseService
from app.services.auth_service import get_current_user, CurrentUser

router = APIRouter()


@router.get("/worklist", response_model=WorklistResponse)
async def get_pharmacy_worklist(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得藥師工作清單
    
    分群顯示：
    - physicianResponse: 醫師回覆（有藥師退回或醫師回應的案件）
    - exceptions: 需逐筆審查（有 FAIL flags）
    - batchEligible: 可批次核准
    - approved: 已批准
    - myClaimed: 我已 Claim
    """
    service = CaseService(db)
    return await service.get_pharmacy_worklist(current_user.subject, status)


@router.post("/cases/{case_id}/claim", response_model=ClaimResponse)
async def claim_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Claim 案件（單人覆核）"""
    service = CaseService(db)
    return await service.claim_case(case_id, current_user)


@router.post("/cases/{case_id}/approve", response_model=ApproveResponse)
async def approve_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """核准案件"""
    service = CaseService(db)
    return await service.approve_case(case_id, current_user)


@router.post("/cases/{case_id}/return", response_model=ReturnResponse)
async def return_case(
    case_id: str,
    request: ReturnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """退回案件給核醫"""
    service = CaseService(db)
    return await service.return_case(case_id, request, current_user)


@router.post("/bulk-approve", response_model=BulkApproveResponse)
async def bulk_approve(
    request: BulkApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """批次核准案件
    
    只有符合批次核准資格的案件會被核准
    """
    service = CaseService(db)
    return await service.bulk_approve(request.caseIds, request.note, current_user)





