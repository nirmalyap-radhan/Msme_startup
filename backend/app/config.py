"""
Backend API Configuration Settings.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class ApiConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Udyog Sathi API"
    app_version: str = "1.0.0"
    app_env: str = Field(default="development", alias="APP_ENV")
    app_secret_key: str = Field(default="dev-secret-key-change-in-production-udyog-sathi", alias="APP_SECRET_KEY")
    api_prefix: str = "/api/v1"
    
    # CORS
    cors_origins_raw: str = Field(default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173", alias="CORS_ORIGINS")
    
    # Token Expiry (minutes)
    jwt_access_token_expire_minutes: int = 60 * 24  # 24 hours

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


api_config = ApiConfig()
