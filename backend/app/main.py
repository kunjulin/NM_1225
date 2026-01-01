"""
NM SMART on FHIR Medication Stewardship - FastAPI 主程式
核子醫學放射藥物用藥治理系統
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.api import nm_router, pharmacy_router, cases_router, analytics_router, demo_router, auth_router, admin_router, settings_router
from app.api.test_data import router as test_data_router
from app.services.outbox_worker import (
    start_outbox_worker, stop_outbox_worker, 
    start_fhir_sync_worker, stop_fhir_sync_worker,
    start_clinical_data_sync_worker, stop_clinical_data_sync_worker
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時初始化資料庫
    await init_db()
    
    # 啟動背景 Worker
    settings = get_settings()
    
    # 啟動 Outbox Worker（處理 MedicationRequest 上傳）
    asyncio.create_task(start_outbox_worker())
    
    # 啟動 FHIR Sync Worker（同步 ServiceRequest）
    if settings.fhir_server_type.value == "thas":
        asyncio.create_task(start_fhir_sync_worker())
    
    # 啟動臨床資料同步 Worker（非同步拉取臨床資料）
    asyncio.create_task(start_clinical_data_sync_worker())
    
    yield
    
    # 關閉時清理資源
    await stop_outbox_worker()
    if settings.fhir_server_type.value == "thas":
        await stop_fhir_sync_worker()
    await stop_clinical_data_sync_worker()


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
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
    app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
    app.include_router(test_data_router, prefix="/api/test-data", tags=["Test Data"])
    
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
