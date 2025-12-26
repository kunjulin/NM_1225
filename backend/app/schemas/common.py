"""
共用 Schema 定義
"""
from typing import Any, Optional
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """錯誤詳情"""
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """標準錯誤回應"""
    error: ErrorDetail


