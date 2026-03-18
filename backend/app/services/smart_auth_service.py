"""
SMART on FHIR 授權服務
處理 OAuth2 授權流程、token 交換、id_token 解析
"""
import json
import uuid
import base64
import logging
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User, UserStatus
from app.fhir.client import FHIRClient

logger = logging.getLogger(__name__)


@dataclass
class SMARTTokenResponse:
    """SMART Token 回應"""
    access_token: str
    token_type: str
    expires_in: int
    scope: str
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None
    patient: Optional[str] = None  # Patient context (if launched with patient)


@dataclass
class SMARTUserInfo:
    """從 id_token 解析的使用者資訊"""
    subject: str  # sub claim
    fhir_user: Optional[str] = None  # fhirUser claim (e.g., "Practitioner/123")
    name: Optional[str] = None
    email: Optional[str] = None


@dataclass
class AuthResult:
    """認證結果"""
    success: bool
    user: Optional[User] = None
    is_new_user: bool = False
    error: Optional[str] = None
    allowed_roles: list[str] = None
    
    def __post_init__(self):
        if self.allowed_roles is None:
            self.allowed_roles = []


@dataclass
class SMARTEndpoints:
    """SMART 授權端點"""
    authorization_endpoint: str
    token_endpoint: str


# 模組層級快取，避免重複請求 .well-known
_discovered_endpoints: Optional[SMARTEndpoints] = None


async def discover_smart_endpoints(fhir_base_url: str, force: bool = False) -> SMARTEndpoints:
    """從 FHIR Server 的 .well-known/smart-configuration 自動發現授權端點
    
    Args:
        fhir_base_url: FHIR Server Base URL
        force: 是否強制重新發現（忽略快取）
        
    Returns:
        SMARTEndpoints 包含 authorization_endpoint 和 token_endpoint
        
    Raises:
        RuntimeError: 無法取得或解析 .well-known/smart-configuration
    """
    global _discovered_endpoints
    if _discovered_endpoints and not force:
        return _discovered_endpoints
    
    well_known_url = f"{fhir_base_url}/.well-known/smart-configuration"
    logger.info(f"正在從 {well_known_url} 發現 SMART 端點...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(well_known_url)
            if response.status_code != 200:
                raise RuntimeError(
                    f"無法取得 SMART configuration ({response.status_code}): {well_known_url}"
                )
            
            config = response.json()
    except httpx.HTTPError as e:
        raise RuntimeError(f"連線 {well_known_url} 失敗: {e}") from e
    
    auth_ep = config.get("authorization_endpoint")
    token_ep = config.get("token_endpoint")
    
    if not auth_ep or not token_ep:
        raise RuntimeError(
            f"SMART configuration 缺少必要欄位: "
            f"authorization_endpoint={'OK' if auth_ep else 'MISSING'}, "
            f"token_endpoint={'OK' if token_ep else 'MISSING'}"
        )
    
    _discovered_endpoints = SMARTEndpoints(
        authorization_endpoint=auth_ep,
        token_endpoint=token_ep,
    )
    logger.info(f"SMART 端點發現成功: auth={auth_ep}, token={token_ep}")
    return _discovered_endpoints


class SMARTAuthService:
    """SMART on FHIR 授權服務"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.fhir_client = FHIRClient()
    
    async def _resolve_endpoints(self) -> SMARTEndpoints:
        """取得授權端點：優先使用手動設定，否則自動發現"""
        if self.settings.smart_authorization_endpoint and self.settings.smart_token_endpoint:
            return SMARTEndpoints(
                authorization_endpoint=self.settings.smart_authorization_endpoint,
                token_endpoint=self.settings.smart_token_endpoint,
            )
        return await discover_smart_endpoints(self.settings.fhir_base_url)
    
    async def get_authorization_url(self, state: str) -> str:
        """產生授權 URL
        
        Args:
            state: 用於防止 CSRF 的隨機字串
            
        Returns:
            THAS 授權頁面 URL
        """
        endpoints = await self._resolve_endpoints()
        
        params = {
            "response_type": "code",
            "client_id": self.settings.smart_client_id,
            "redirect_uri": self.settings.smart_redirect_uri,
            "scope": self.settings.smart_scopes,
            "state": state,
            "aud": self.settings.fhir_base_url,
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{endpoints.authorization_endpoint}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, token_endpoint_override: Optional[str] = None) -> Optional[SMARTTokenResponse]:
        """用授權碼換取 access token
        
        Args:
            code: 授權碼
            token_endpoint_override: 動態 token 端點（EHR Launch 時使用）
            
        Returns:
            Token 回應，失敗時返回 None
        """
        if token_endpoint_override:
            token_endpoint = token_endpoint_override
        else:
            endpoints = await self._resolve_endpoints()
            token_endpoint = endpoints.token_endpoint
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.settings.smart_redirect_uri,
            "client_id": self.settings.smart_client_id,
        }
        
        if self.settings.smart_client_secret:
            data["client_secret"] = self.settings.smart_client_secret
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    return SMARTTokenResponse(
                        access_token=token_data.get("access_token", ""),
                        token_type=token_data.get("token_type", "Bearer"),
                        expires_in=token_data.get("expires_in", 3600),
                        scope=token_data.get("scope", ""),
                        id_token=token_data.get("id_token"),
                        refresh_token=token_data.get("refresh_token"),
                        patient=token_data.get("patient"),
                    )
                else:
                    logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return None
    
    def parse_id_token(self, id_token: str) -> Optional[SMARTUserInfo]:
        """解析 id_token（不驗證簽名，僅用於 demo/開發環境）
        
        注意：生產環境應該驗證 JWT 簽名
        
        Args:
            id_token: JWT 格式的 id_token
            
        Returns:
            使用者資訊
        """
        try:
            # JWT 分為三部分：header.payload.signature
            parts = id_token.split(".")
            if len(parts) != 3:
                logger.error("Invalid id_token format")
                return None
            
            # 解碼 payload（第二部分）
            payload_b64 = parts[1]
            # 補齊 padding
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            
            payload_json = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_json)
            
            return SMARTUserInfo(
                subject=payload.get("sub", ""),
                fhir_user=payload.get("fhirUser"),
                name=payload.get("name"),
                email=payload.get("email"),
            )
            
        except Exception as e:
            logger.error(f"Failed to parse id_token: {e}")
            return None
    
    async def get_practitioner_info(self, practitioner_ref: str) -> dict:
        """從 FHIR Server 取得 Practitioner 資訊
        
        Args:
            practitioner_ref: Practitioner 參考（如 "Practitioner/123"）
            
        Returns:
            Practitioner 資源
        """
        try:
            result = await self.fhir_client._request("GET", practitioner_ref)
            return result or {}
        except Exception as e:
            logger.error(f"Failed to get Practitioner: {e}")
            return {}
    
    async def authenticate_with_code(self, code: str, token_endpoint_override: Optional[str] = None) -> AuthResult:
        """完整的 SMART 認證流程
        
        1. 用授權碼換取 token
        2. 解析 id_token 取得使用者資訊
        3. 從 FHIR Server 取得 Practitioner 資訊
        4. 查詢或建立本地使用者
        
        Args:
            code: 授權碼
            token_endpoint_override: 動態 token 端點（EHR Launch 時使用）
            
        Returns:
            認證結果
        """
        # Step 1: 換取 token
        token_response = await self.exchange_code_for_token(code, token_endpoint_override)
        if not token_response:
            return AuthResult(success=False, error="Token exchange failed")
        
        # Step 2: 解析 id_token
        user_info = None
        if token_response.id_token:
            user_info = self.parse_id_token(token_response.id_token)
        
        if not user_info or not user_info.subject:
            return AuthResult(success=False, error="Failed to parse user info from id_token")
        
        # Step 3: 取得 Practitioner 資訊（如果有 fhirUser）
        practitioner_name = user_info.name
        if user_info.fhir_user and user_info.fhir_user.startswith("Practitioner/"):
            practitioner_info = await self.get_practitioner_info(user_info.fhir_user)
            if practitioner_info:
                # 嘗試從 Practitioner 資源取得名稱
                names = practitioner_info.get("name", [])
                if names:
                    name_obj = names[0]
                    practitioner_name = name_obj.get("text") or f"{name_obj.get('family', '')} {name_obj.get('given', [''])[0]}".strip()
        
        # Step 4: 查詢或建立本地使用者
        result = await self.db.execute(
            select(User).where(User.subject == user_info.subject)
        )
        existing_user = result.scalar_one_or_none()
        
        now = datetime.now(timezone.utc).isoformat()
        
        if existing_user:
            # 更新最後登入時間
            existing_user.last_login_at = now
            existing_user.updated_at = now
            
            # 如果有新的 Practitioner 參考，更新
            if user_info.fhir_user and not existing_user.practitioner_ref:
                existing_user.practitioner_ref = user_info.fhir_user
            
            await self.db.commit()
            
            # 解析允許的角色
            allowed_roles = json.loads(existing_user.allowed_roles or "[]")
            
            return AuthResult(
                success=True,
                user=existing_user,
                is_new_user=False,
                allowed_roles=allowed_roles,
            )
        else:
            # 建立新使用者（狀態為 PENDING）
            new_user = User(
                id=str(uuid.uuid4()),
                subject=user_info.subject,
                practitioner_ref=user_info.fhir_user,
                display_name=practitioner_name or user_info.subject,
                email=user_info.email,
                allowed_roles="[]",  # 待管理員指派
                status=UserStatus.PENDING.value,
                is_admin=False,
                last_login_at=now,
                created_at=now,
                updated_at=now,
            )
            self.db.add(new_user)
            await self.db.commit()
            
            return AuthResult(
                success=True,
                user=new_user,
                is_new_user=True,
                allowed_roles=[],
            )
    
    async def get_user_by_subject(self, subject: str) -> Optional[User]:
        """根據 subject 查詢使用者
        
        Args:
            subject: 使用者識別碼
            
        Returns:
            使用者，不存在時返回 None
        """
        result = await self.db.execute(
            select(User).where(User.subject == subject)
        )
        return result.scalar_one_or_none()
    
    async def validate_user_role(self, subject: str, acting_role: str) -> tuple[bool, Optional[User], str]:
        """驗證使用者是否有指定角色的權限
        
        Args:
            subject: 使用者識別碼
            acting_role: 要驗證的角色
            
        Returns:
            (is_valid, user, error_message)
        """
        user = await self.get_user_by_subject(subject)
        
        if not user:
            return False, None, "User not found"
        
        if user.status == UserStatus.PENDING.value:
            return False, user, "User account is pending approval"
        
        if user.status == UserStatus.INACTIVE.value:
            return False, user, "User account is inactive"
        
        allowed_roles = json.loads(user.allowed_roles or "[]")
        
        # ADMIN 可以使用任何角色
        if "ADMIN" in allowed_roles:
            return True, user, ""
        
        if acting_role not in allowed_roles:
            return False, user, f"User does not have {acting_role} role"
        
        return True, user, ""






