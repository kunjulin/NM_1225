"""
NM SMART on FHIR Medication Stewardship - FastAPI 主程式
核子醫學放射藥物用藥治理系統
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.api import nm_router, pharmacy_router, cases_router, analytics_router, demo_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時初始化資料庫
    await init_db()
    yield
    # 關閉時清理資源（如需要）


def create_app() -> FastAPI:
    """建立 FastAPI 應用程式"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="核子醫學放射藥物用藥治理與臨床決策支援系統",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    
    # CORS 設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 註冊路由
    app.include_router(nm_router, prefix="/api/nm", tags=["NM Physician"])
    app.include_router(pharmacy_router, prefix="/api/pharmacy", tags=["Pharmacy"])
    app.include_router(cases_router, prefix="/api/cases", tags=["Cases"])
    app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
    
    # Demo Mode 專用路由
    if settings.is_demo_mode:
        app.include_router(demo_router, prefix="/api/demo", tags=["Demo"])
    
    @app.get("/api/health")
    async def health_check():
        """健康檢查端點"""
        return {
            "status": "healthy",
            "app_mode": settings.app_mode.value,
            "fhir_server": settings.fhir_server_type.value,
            "fhir_base_url": settings.fhir_base_url,
        }
    
    @app.get("/api/config")
    async def get_config():
        """取得公開設定資訊"""
        return {
            "appName": settings.app_name,
            "appVersion": settings.app_version,
            "appMode": settings.app_mode.value,
            "fhirServerType": settings.fhir_server_type.value,
            "isDemo": settings.is_demo_mode,
        }
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


