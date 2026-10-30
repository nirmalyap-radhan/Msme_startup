"""
Configuration settings for Scheme Ingestion and Document Processing Pipeline.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class IngestionConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    
    # Storage settings
    raw_storage_dir: str = Field(default="./data/raw", alias="DOCUMENT_STORAGE_PATH")
    processed_storage_dir: str = Field(default="./data/processed", alias="PROCESSED_STORAGE_PATH")
    
    # Ingestion Allowlist & Network
    scheme_source_allowlist_raw: str = Field(
        default="msme.odisha.gov.in,odishamsme.nic.in,msme.gov.in,myscheme.gov.in",
        alias="SCHEME_SOURCE_ALLOWLIST"
    )
    user_agent: str = Field(
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) UdyogSathiBot/1.0 (MSME Odisha Scheme Discovery; contact@udyogsathi.odisha.gov.in)",
        alias="INGESTION_USER_AGENT"
    )
    request_timeout_seconds: int = Field(default=30, alias="INGESTION_TIMEOUT_SECONDS")
    max_retries: int = Field(default=3, alias="INGESTION_MAX_RETRIES")
    
    # OCR Settings
    ocr_languages: str = Field(default="ori,hin,eng", alias="OCR_LANGUAGE_DATA")
    ocr_char_density_threshold: int = Field(default=100, alias="OCR_CHAR_DENSITY_THRESHOLD")
    
    # Database URL
    database_url: str = Field(
        default="sqlite:///./data/udyog_sathi.db",
        alias="DATABASE_URL"
    )

    @property
    def source_allowlist(self) -> List[str]:
        return [domain.strip().lower() for domain in self.scheme_source_allowlist_raw.split(",") if domain.strip()]

    @property
    def tesseract_lang_string(self) -> str:
        # Tesseract language parameter syntax: 'ori+hin+eng'
        langs = [l.strip() for l in self.ocr_languages.split(",") if l.strip()]
        return "+".join(langs) if langs else "eng"


# Global ingestion config instance
ingestion_config = IngestionConfig()
