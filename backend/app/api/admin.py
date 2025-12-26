"""
管理員 API 路由
使用者管理與系統設定
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User, UserStatus
from app.services.auth_service import get_current_user, CurrentUser
from app.schemas.case import ActingRole

router = APIRouter()


# === Schemas ===

class UserListItem(BaseModel):
    """使用者列表項目"""
    id: str
    subject: str
    display_name: str
    practitioner_ref: Optional[str] = None
    email: Optional[str] = None
    status: str
    allowed_roles: List[str]
    is_admin: bool
    last_login_at: Optional[str] = None
    created_at: str
    updated_at: str


class UserListResponse(BaseModel):
    """使用者列表回應"""
    users: List[UserListItem]
    total: int
    pending_count: int


class ApproveUserRequest(BaseModel):
    """審核使用者請求"""
    allowed_roles: List[str]


class UpdateUserRequest(BaseModel):
    """更新使用者請求"""
    display_name: Optional[str] = None
    email: Optional[str] = None
    allowed_roles: Optional[List[str]] = None


class CreateUserRequest(BaseModel):
    """手動建立使用者請求"""
    subject: str
    display_name: str
    email: Optional[str] = None
    allowed_roles: List[str]


class UserResponse(BaseModel):
    """使用者回應"""
    id: str
    subject: str
    display_name: str
    practitioner_ref: Optional[str] = None
    email: Optional[str] = None
    status: str
    allowed_roles: List[str]
    is_admin: bool


# === Helper Functions ===

def require_admin(current_user: CurrentUser):
    """檢查是否為管理員"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


def user_to_response(user: User) -> UserListItem:
    """轉換 User 為回應格式"""
    return UserListItem(
        id=user.id,
        subject=user.subject,
        display_name=user.display_name,
        practitioner_ref=user.practitioner_ref,
        email=user.email,
        status=user.status,
        allowed_roles=json.loads(user.allowed_roles or "[]"),
        is_admin=user.is_admin,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# === Endpoints ===

@router.get("/users", response_model=UserListResponse)
async def list_users(
    status_filter: Optional[str] = Query(None, alias="status", description="篩選狀態"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得使用者列表
    
    只有管理員可以存取
    """
    require_admin(current_user)
    
    # 建構查詢
    query = select(User)
    
    if status_filter:
        query = query.where(User.status == status_filter)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.subject.ilike(search_pattern),
                User.display_name.ilike(search_pattern),
                User.email.ilike(search_pattern),
            )
        )
    
    query = query.order_by(User.created_at.desc())
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    # 計算待審核數量
    pending_result = await db.execute(
        select(User).where(User.status == UserStatus.PENDING.value)
    )
    pending_count = len(pending_result.scalars().all())
    
    return UserListResponse(
        users=[user_to_response(u) for u in users],
        total=len(users),
        pending_count=pending_count,
    )


@router.get("/users/pending", response_model=UserListResponse)
async def list_pending_users(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得待審核使用者列表
    
    只有管理員可以存取
    """
    require_admin(current_user)
    
    result = await db.execute(
        select(User)
        .where(User.status == UserStatus.PENDING.value)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    return UserListResponse(
        users=[user_to_response(u) for u in users],
        total=len(users),
        pending_count=len(users),
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """取得單一使用者詳情
    
    只有管理員可以存取
    """
    require_admin(current_user)
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        subject=user.subject,
        display_name=user.display_name,
        practitioner_ref=user.practitioner_ref,
        email=user.email,
        status=user.status,
        allowed_roles=json.loads(user.allowed_roles or "[]"),
        is_admin=user.is_admin,
    )


@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """手動建立使用者
    
    只有管理員可以存取
    """
    require_admin(current_user)
    
    # 檢查 subject 是否已存在
    existing = await db.execute(
        select(User).where(User.subject == request.subject)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this subject already exists"
        )
    
    # 驗證角色
    valid_roles = [r.value for r in ActingRole]
    for role in request.allowed_roles:
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}. Must be one of: {valid_roles}"
            )
    
    now = datetime.now(timezone.utc).isoformat()
    
    new_user = User(
        id=str(uuid.uuid4()),
        subject=request.subject,
        practitioner_ref=None,
        display_name=request.display_name,
        email=request.email,
        allowed_roles=json.dumps(request.allowed_roles),
        status=UserStatus.ACTIVE.value,  # 手動建立的使用者直接啟用
        is_admin="ADMIN" in request.allowed_roles,
        last_login_at=None,
        created_at=now,
        updated_at=now,
    )
    
    db.add(new_user)
    await db.commit()
    
    return UserResponse(
        id=new_user.id,
        subject=new_user.subject,
        display_name=new_user.display_name,
        practitioner_ref=new_user.practitioner_ref,
        email=new_user.email,
        status=new_user.status,
        allowed_roles=request.allowed_roles,
        is_admin=new_user.is_admin,
    )


@router.post("/users/{user_id}/approve", response_model=UserResponse)
async def approve_user(
    user_id: str,
    request: ApproveUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """審核通過使用者並指派角色
    
    只有管理員可以存取
    """
    require_admin(current_user)
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.status != UserStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User is not in PENDING status (current: {user.status})"
        )
    
    # 驗證角色
    valid_roles = [r.value for r in ActingRole]
    for role in request.allowed_roles:
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}. Must be one of: {valid_roles}"
            )
    
    if not request.allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one role must be assigned"
        )
    
    # 更新使用者
    user.status = UserStatus.ACTIVE.value
    user.allowed_roles = json.dumps(request.allowed_roles)
    user.is_admin = "ADMIN" in request.allowed_roles
    user.updated_at = datetime.now(timezone.utc).isoformat()
    
    await db.commit()
    
    return UserResponse(
        id=user.id,
        subject=user.subject,
        display_name=user.display_name,
        practitioner_ref=user.practitioner_ref,
        email=user.email,
        status=user.status,
        allowed_roles=request.allowed_roles,
        is_admin=user.is_admin,
    )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """更新使用者資訊
    
    只有管理員可以存取
    """
    require_admin(current_user)
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 更新欄位
    if request.display_name is not None:
        user.display_name = request.display_name
    
    if request.email is not None:
        user.email = request.email
    
    if request.allowed_roles is not None:
        # 驗證角色
        valid_roles = [r.value for r in ActingRole]
        for role in request.allowed_roles:
            if role not in valid_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {role}. Must be one of: {valid_roles}"
                )
        
        user.allowed_roles = json.dumps(request.allowed_roles)
        user.is_admin = "ADMIN" in request.allowed_roles
    
    user.updated_at = datetime.now(timezone.utc).isoformat()
    
    await db.commit()
    
    return UserResponse(
        id=user.id,
        subject=user.subject,
        display_name=user.display_name,
        practitioner_ref=user.practitioner_ref,
        email=user.email,
        status=user.status,
        allowed_roles=json.loads(user.allowed_roles or "[]"),
        is_admin=user.is_admin,
    )


@router.post("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """啟用使用者
    
    只有管理員可以存取
    """
    require_admin(current_user)
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.status == UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already active"
        )
    
    user.status = UserStatus.ACTIVE.value
    user.updated_at = datetime.now(timezone.utc).isoformat()
    
    await db.commit()
    
    return UserResponse(
        id=user.id,
        subject=user.subject,
        display_name=user.display_name,
        practitioner_ref=user.practitioner_ref,
        email=user.email,
        status=user.status,
        allowed_roles=json.loads(user.allowed_roles or "[]"),
        is_admin=user.is_admin,
    )


@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """停用使用者
    
    只有管理員可以存取
    """
    require_admin(current_user)
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 不能停用自己
    if user.subject == current_user.subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    user.status = UserStatus.INACTIVE.value
    user.updated_at = datetime.now(timezone.utc).isoformat()
    
    await db.commit()
    
    return UserResponse(
        id=user.id,
        subject=user.subject,
        display_name=user.display_name,
        practitioner_ref=user.practitioner_ref,
        email=user.email,
        status=user.status,
        allowed_roles=json.loads(user.allowed_roles or "[]"),
        is_admin=user.is_admin,
    )


