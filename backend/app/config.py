"""
應用程式設定模組
支援 Production Mode 與 Demo Mode 切換
支援 Local HAPI FHIR 與 THAS 競賽環境切換
"""
from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class AppMode(str, Enum):
    """應用程式執行模式"""
    PRODUCTION = "production"
    DEMO = "demo"


class FHIRServerType(str, Enum):
    """FHIR Server 類型"""
    LOCAL = "local"
    THAS = "thas"


class Settings(BaseSettings):
    """應用程式設定"""
    
    # 應用程式模式
    app_mode: AppMode = AppMode.DEMO
    app_name: str = "NM Medication Stewardship"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 資料庫設定
    database_url: str = "sqlite:///./nm_stewardship.db"
    
    # FHIR Server 設定
    fhir_server_type: FHIRServerType = FHIRServerType.LOCAL
    
    # Local HAPI FHIR Server
    fhir_local_base_url: str = "http://localhost:8080/fhir"
    
    # THAS 競賽環境
    fhir_thas_base_url: str = "https://thas.mohw.gov.tw/v/r4/sim/WzIsIiIsIiIsIkFVVE8iLDAsMCwwLCIiLCIiLCIiLCIiLCIiLCIiLCIiLDAsMSwiIl0/fhir"
    
    # FHIR Client 設定
    fhir_timeout_seconds: float = 5.0
    fhir_retry_count: int = 3
    
    # Outbox Worker 設定
    outbox_poll_interval_seconds: float = 10.0
    outbox_max_retries: int = 5
    
    # CORS 設定 (for frontend)
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    @property
    def fhir_base_url(self) -> str:
        """取得目前使用的 FHIR Server Base URL"""
        if self.fhir_server_type == FHIRServerType.THAS:
            return self.fhir_thas_base_url
        return self.fhir_local_base_url
    
    @property
    def is_demo_mode(self) -> bool:
        """是否為 Demo Mode"""
        return self.app_mode == AppMode.DEMO
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # 支援環境變數前綴，例如 NM_APP_MODE=demo
        env_prefix = "NM_"


@lru_cache
def get_settings() -> Settings:
    """取得設定單例"""
    return Settings()

