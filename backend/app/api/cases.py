"""
Cases API 路由
病人快照與 Auto-fill 功能
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
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
from app.services.llm_service import LLMService
from app.models import TriggerType

router = APIRouter()


# === LLM Analysis Schemas ===

class LLMAnalysisResponse(BaseModel):
    """LLM 分析回應"""
    id: str
    caseId: str
    status: str
    result: Optional[dict] = None
    errorMessage: Optional[str] = None
    latencyMs: Optional[int] = None
    createdAt: Optional[str] = None


class LLMAnalysisTriggerRequest(BaseModel):
    """觸發 LLM 分析請求"""
    trigger_type: str = "MANUAL"  # MANUAL or AUTO


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


# === LLM Analysis Endpoints ===

@router.post("/{case_id}/llm-analysis", response_model=LLMAnalysisResponse)
async def trigger_llm_analysis(
    case_id: str,
    request: LLMAnalysisTriggerRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """觸發 LLM 臨床分析
    
    基於 FHIR snapshot 和 CDS flags，使用 LLM 產生：
    - 病例摘要
    - 適應症評估
    - CDSS 整合建議
    """
    trigger_type = TriggerType.MANUAL
    if request and request.trigger_type == "AUTO":
        trigger_type = TriggerType.AUTO
    
    llm_service = LLMService(db)
    result = await llm_service.analyze_case(
        case_id=case_id,
        triggered_by=current_user.subject,
        trigger_type=trigger_type,
    )
    
    return LLMAnalysisResponse(
        id=result.id,
        caseId=result.case_id,
        status=result.status,
        result=result.result,
        errorMessage=result.error_message,
        latencyMs=result.latency_ms,
        createdAt=result.created_at,
    )


@router.get("/{case_id}/llm-analysis", response_model=Optional[LLMAnalysisResponse])
async def get_latest_llm_analysis(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得最近的 LLM 分析結果
    
    如果沒有分析結果，回傳 null
    """
    llm_service = LLMService(db)
    result = await llm_service.get_latest_analysis(case_id)
    
    if not result:
        return None
    
    return LLMAnalysisResponse(
        id=result.id,
        caseId=result.case_id,
        status=result.status,
        result=result.result,
        errorMessage=result.error_message,
        latencyMs=result.latency_ms,
        createdAt=result.created_at,
    )


@router.get("/{case_id}/llm-analysis/history")
async def get_llm_analysis_history(
    case_id: str,
    limit: int = Query(10, description="最大筆數"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得 LLM 分析歷史
    
    按時間倒序排列
    """
    llm_service = LLMService(db)
    results = await llm_service.get_analysis_history(case_id, limit=limit)
    
    return {
        "analyses": [
            LLMAnalysisResponse(
                id=r.id,
                caseId=r.case_id,
                status=r.status,
                result=r.result,
                errorMessage=r.error_message,
                latencyMs=r.latency_ms,
                createdAt=r.created_at,
            ).model_dump()
            for r in results
        ],
        "total": len(results),
    }


@router.get("/{case_id}/llm-settings")
async def get_llm_settings_for_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得 LLM 設定狀態（用於前端判斷是否顯示分析按鈕）
    
    回傳 LLM 是否已設定、是否啟用自動分析
    """
    llm_service = LLMService(db)
    settings = await llm_service.get_settings()
    
    return {
        "isConfigured": settings.is_configured(),
        "autoAnalyze": settings.auto_analyze,
    }

