"""
認證 API 路由
SMART on FHIR OAuth2 授權流程
"""
import json
import logging
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.config import get_settings
from app.services.smart_auth_service import SMARTAuthService
from app.models.user import User, UserStatus

logger = logging.getLogger(__name__)
router = APIRouter()


# === Schemas ===

class SMARTLaunchResponse(BaseModel):
    """SMART Launch 回應"""
    authorization_url: str
    state: str


class SMARTCallbackRequest(BaseModel):
    """SMART Callback 請求"""
    code: str
    state: str


class EHRLunchRequest(BaseModel):
    """EHR Launch 請求"""
    iss: str  # Issuer URL
    launch: str  # Launch parameter


class AuthResultResponse(BaseModel):
    """認證結果回應"""
    success: bool
    subject: Optional[str] = None
    display_name: Optional[str] = None
    practitioner_ref: Optional[str] = None
    status: Optional[str] = None
    allowed_roles: list[str] = []
    is_new_user: bool = False
    error: Optional[str] = None


class UserInfoResponse(BaseModel):
    """使用者資訊回應"""
    subject: str
    display_name: str
    practitioner_ref: Optional[str] = None
    email: Optional[str] = None
    status: str
    allowed_roles: list[str]
    is_admin: bool


class ConfigResponse(BaseModel):
    """SMART 設定回應（公開資訊）"""
    is_demo_mode: bool
    smart_enabled: bool
    authorization_endpoint: Optional[str] = None
    client_id: Optional[str] = None
    redirect_uri: Optional[str] = None


# === Endpoints ===

@router.get("/config", response_model=ConfigResponse)
async def get_auth_config():
    """取得認證設定（公開資訊）
    
    用於前端判斷是否啟用 SMART 登入
    """
    settings = get_settings()
    
    smart_enabled = bool(
        settings.smart_client_id and 
        settings.smart_authorization_endpoint and 
        settings.smart_token_endpoint
    )
    
    return ConfigResponse(
        is_demo_mode=settings.is_demo_mode,
        smart_enabled=smart_enabled,
        authorization_endpoint=settings.smart_authorization_endpoint if smart_enabled else None,
        client_id=settings.smart_client_id if smart_enabled else None,
        redirect_uri=settings.smart_redirect_uri if smart_enabled else None,
    )


@router.get("/smart/launch", response_model=SMARTLaunchResponse)
async def smart_launch():
    """啟動 SMART on FHIR 授權流程
    
    產生授權 URL 並回傳，前端將重導向到此 URL
    """
    settings = get_settings()
    
    if not settings.smart_client_id or not settings.smart_authorization_endpoint:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SMART on FHIR is not configured"
        )
    
    # 產生 state 用於防止 CSRF
    state = secrets.token_urlsafe(32)
    
    # 建構授權 URL
    params = {
        "response_type": "code",
        "client_id": settings.smart_client_id,
        "redirect_uri": settings.smart_redirect_uri,
        "scope": "openid fhirUser profile",
        "state": state,
        "aud": settings.fhir_base_url,
    }
    
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    authorization_url = f"{settings.smart_authorization_endpoint}?{query_string}"
    
    return SMARTLaunchResponse(
        authorization_url=authorization_url,
        state=state,
    )


class SMARTCallbackRequestWithTokenEndpoint(BaseModel):
    """SMART Callback 請求（含動態 token 端點）"""
    code: str
    state: str
    token_endpoint: Optional[str] = None  # EHR Launch 時需要


@router.post("/smart/callback", response_model=AuthResultResponse)
async def smart_callback(
    request: SMARTCallbackRequestWithTokenEndpoint,
    db: AsyncSession = Depends(get_db),
):
    """處理 SMART on FHIR 授權回呼（標準授權碼流程或 EHR Launch）
    
    1. 用授權碼換取 token（使用動態或預設的 token 端點）
    2. 解析 id_token 取得使用者資訊
    3. 查詢或建立本地使用者
    """
    auth_service = SMARTAuthService(db)
    
    # 如果有提供動態 token 端點（EHR Launch），暫時更新設定
    original_token_endpoint = None
    if request.token_endpoint:
        original_token_endpoint = auth_service.settings.smart_token_endpoint
        auth_service.settings.smart_token_endpoint = request.token_endpoint
    
    try:
        result = await auth_service.authenticate_with_code(request.code)
        
        if not result.success:
            return AuthResultResponse(
                success=False,
                error=result.error,
            )
        
        user = result.user
        
        return AuthResultResponse(
            success=True,
            subject=user.subject,
            display_name=user.display_name,
            practitioner_ref=user.practitioner_ref,
            status=user.status,
            allowed_roles=result.allowed_roles,
            is_new_user=result.is_new_user,
        )
    finally:
        # 恢復原始 token 端點
        if original_token_endpoint:
            auth_service.settings.smart_token_endpoint = original_token_endpoint


@router.post("/smart/ehr-launch-url")
async def smart_ehr_launch_url(
    request: EHRLunchRequest,
):
    """取得 EHR Launch 授權 URL
    
    用於 EHR Launch 模式，返回需要重導向的授權 URL
    同時返回 token_endpoint 以便後續使用
    """
    import httpx
    
    try:
        # 從 iss 取得 SMART 設定
        well_known_url = f"{request.iss}/.well-known/smart-configuration"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            config_response = await client.get(well_known_url)
            if config_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to get SMART configuration from {well_known_url}",
                )
            
            smart_config = config_response.json()
        
        # 取得授權端點和 token 端點
        authorization_endpoint = smart_config.get("authorization_endpoint")
        token_endpoint = smart_config.get("token_endpoint")
        
        if not authorization_endpoint:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SMART configuration missing authorization_endpoint",
            )
        
        if not token_endpoint:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SMART configuration missing token_endpoint",
            )
        
        settings = get_settings()
        
        # 建構授權 URL（包含 launch 參數）
        state = secrets.token_urlsafe(32)
        params = {
            "response_type": "code",
            "client_id": settings.smart_client_id,
            "redirect_uri": settings.smart_redirect_uri,
            "scope": "openid fhirUser profile",
            "state": state,
            "aud": request.iss,
            "launch": request.launch,  # EHR Launch 關鍵參數
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        authorization_url = f"{authorization_endpoint}?{query_string}"
        
        return {
            "authorization_url": authorization_url,
            "state": state,
            "token_endpoint": token_endpoint,  # 返回 token 端點供後續使用
            "iss": request.iss,  # 返回 iss 供後續使用
        }
        
    except Exception as e:
        logger.error(f"EHR Launch URL error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get EHR Launch URL: {str(e)}",
        )


@router.get("/user-info", response_model=UserInfoResponse)
async def get_user_info(
    subject: str = Query(..., description="使用者識別碼"),
    db: AsyncSession = Depends(get_db),
):
    """查詢使用者資訊
    
    用於登入頁面查詢使用者允許的角色
    """
    auth_service = SMARTAuthService(db)
    user = await auth_service.get_user_by_subject(subject)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    allowed_roles = json.loads(user.allowed_roles or "[]")
    
    return UserInfoResponse(
        subject=user.subject,
        display_name=user.display_name,
        practitioner_ref=user.practitioner_ref,
        email=user.email,
        status=user.status,
        allowed_roles=allowed_roles,
        is_admin=user.is_admin,
    )


@router.post("/validate-role")
async def validate_user_role(
    subject: str = Query(..., description="使用者識別碼"),
    acting_role: str = Query(..., description="要驗證的角色"),
    db: AsyncSession = Depends(get_db),
):
    """驗證使用者是否有指定角色的權限
    
    用於 Production Mode 下的角色驗證
    """
    auth_service = SMARTAuthService(db)
    is_valid, user, error = await auth_service.validate_user_role(subject, acting_role)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error
        )
    
    return {
        "valid": True,
        "subject": user.subject,
        "acting_role": acting_role,
    }


