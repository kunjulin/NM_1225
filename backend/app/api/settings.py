"""
Settings API
系統設定相關 API（包含 LLM 設定）
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.services.auth_service import get_current_user, CurrentUser
from app.services.llm_service import LLMService, LLMSettings
from app.models import DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT_TEMPLATE

router = APIRouter()


# === Request/Response Schemas ===

class LLMSettingsRequest(BaseModel):
    """LLM 設定更新請求"""
    endpoint_url: str = Field(..., description="LLM API Endpoint URL")
    model_name: str = Field(default="gpt-4", description="模型名稱")
    api_key: Optional[str] = Field(default=None, description="API Key（可選）")
    system_prompt: str = Field(default="", description="System Prompt")
    user_prompt_template: str = Field(default="", description="User Prompt Template")
    auto_analyze: bool = Field(default=False, description="是否自動分析")
    timeout_seconds: float = Field(default=60.0, description="請求超時秒數")
    max_tokens: int = Field(default=4096, description="最大 tokens")
    temperature: float = Field(default=0.1, description="Temperature 參數")
    disable_thinking_mode: bool = Field(default=False, description="是否禁用 thinking mode")


class LLMSettingsResponse(BaseModel):
    """LLM 設定回應"""
    endpoint_url: str
    model_name: str
    has_api_key: bool
    system_prompt: str
    user_prompt_template: str
    auto_analyze: bool
    timeout_seconds: float
    max_tokens: int
    temperature: float
    disable_thinking_mode: bool
    is_configured: bool


class LLMTestConnectionResponse(BaseModel):
    """LLM 連線測試回應"""
    success: bool
    message: str
    latency_ms: Optional[int] = None


class LLMDefaultPromptsResponse(BaseModel):
    """LLM 預設提示詞回應"""
    system_prompt: str
    user_prompt_template: str


# === API Endpoints ===

@router.get("/llm", response_model=LLMSettingsResponse)
async def get_llm_settings(
    current_user: CurrentUser = Depends(get_current_user),
    db = Depends(get_db),
):
    """取得 LLM 設定
    
    僅管理員可存取
    """
    # 檢查權限：僅 ADMIN 可存取
    if current_user.acting_role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理員可以存取設定"
        )
    
    llm_service = LLMService(db)
    settings = await llm_service.get_settings()
    
    return LLMSettingsResponse(
        endpoint_url=settings.endpoint_url,
        model_name=settings.model_name,
        has_api_key=bool(settings.api_key),
        system_prompt=settings.system_prompt,
        user_prompt_template=settings.user_prompt_template,
        auto_analyze=settings.auto_analyze,
        timeout_seconds=settings.timeout_seconds,
        max_tokens=settings.max_tokens,
        temperature=settings.temperature,
        disable_thinking_mode=settings.disable_thinking_mode,
        is_configured=settings.is_configured(),
    )


@router.put("/llm", response_model=LLMSettingsResponse)
async def update_llm_settings(
    request: LLMSettingsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db = Depends(get_db),
):
    """更新 LLM 設定
    
    僅管理員可更新
    """
    # 檢查權限：僅 ADMIN 可更新
    if current_user.acting_role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理員可以更新設定"
        )
    
    llm_service = LLMService(db)
    
    # 如果沒有提供 api_key，保留原有的
    existing_settings = await llm_service.get_settings()
    api_key = request.api_key if request.api_key is not None else existing_settings.api_key
    
    settings = LLMSettings(
        endpoint_url=request.endpoint_url,
        model_name=request.model_name,
        api_key=api_key,
        system_prompt=request.system_prompt,
        user_prompt_template=request.user_prompt_template,
        auto_analyze=request.auto_analyze,
        timeout_seconds=request.timeout_seconds,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        disable_thinking_mode=request.disable_thinking_mode,
    )
    
    await llm_service.save_settings(settings)
    
    return LLMSettingsResponse(
        endpoint_url=settings.endpoint_url,
        model_name=settings.model_name,
        has_api_key=bool(settings.api_key),
        system_prompt=settings.system_prompt,
        user_prompt_template=settings.user_prompt_template,
        auto_analyze=settings.auto_analyze,
        timeout_seconds=settings.timeout_seconds,
        max_tokens=settings.max_tokens,
        temperature=settings.temperature,
        disable_thinking_mode=settings.disable_thinking_mode,
        is_configured=settings.is_configured(),
    )


@router.post("/llm/test", response_model=LLMTestConnectionResponse)
async def test_llm_connection(
    current_user: CurrentUser = Depends(get_current_user),
    db = Depends(get_db),
):
    """測試 LLM 連線
    
    僅管理員可測試
    """
    # 檢查權限：僅 ADMIN 可測試
    if current_user.acting_role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理員可以測試連線"
        )
    
    llm_service = LLMService(db)
    result = await llm_service.test_connection()
    
    return LLMTestConnectionResponse(
        success=result["success"],
        message=result["message"],
        latency_ms=result["latency_ms"],
    )


@router.get("/llm/defaults", response_model=LLMDefaultPromptsResponse)
async def get_default_prompts(
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得預設提示詞
    
    僅管理員可存取
    """
    # 檢查權限：僅 ADMIN 可存取
    if current_user.acting_role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理員可以存取設定"
        )
    
    return LLMDefaultPromptsResponse(
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE,
    )


@router.delete("/llm/api-key")
async def clear_api_key(
    current_user: CurrentUser = Depends(get_current_user),
    db = Depends(get_db),
):
    """清除 API Key
    
    僅管理員可清除
    """
    # 檢查權限：僅 ADMIN 可清除
    if current_user.acting_role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理員可以清除 API Key"
        )
    
    llm_service = LLMService(db)
    settings = await llm_service.get_settings()
    settings.api_key = ""
    await llm_service.save_settings(settings)
    
    return {"success": True, "message": "API Key 已清除"}


@router.get("/llm/error-logs")
async def get_llm_error_logs(
    limit: int = Query(50, description="最大筆數"),
    case_id: Optional[str] = Query(None, description="案件 ID 過濾（可選）"),
    current_user: CurrentUser = Depends(get_current_user),
    db = Depends(get_db),
):
    """取得 LLM 分析錯誤記錄
    
    僅管理員可存取
    
    Args:
        limit: 最大筆數（預設 50）
        case_id: 可選的案件 ID 過濾
    """
    # 檢查權限：僅 ADMIN 可存取
    if current_user.acting_role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理員可以存取錯誤記錄"
        )
    
    from app.api.cases import LLMAnalysisResponse
    
    llm_service = LLMService(db)
    results = await llm_service.get_failed_analyses(limit=limit, case_id=case_id)
    
    return {
        "errors": [
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