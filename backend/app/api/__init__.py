"""
API 路由模組
"""
from app.api.nm import router as nm_router
from app.api.pharmacy import router as pharmacy_router
from app.api.cases import router as cases_router
from app.api.analytics import router as analytics_router
from app.api.demo import router as demo_router

__all__ = [
    "nm_router",
    "pharmacy_router", 
    "cases_router",
    "analytics_router",
    "demo_router",
]


