"""
FinPilot AI — Application Configuration
========================================
Centralized settings management using Pydantic BaseSettings.
All configuration is loaded from environment variables with
sensible defaults for development.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide settings loaded from environment variables.
    Uses pydantic-settings for automatic type coercion and validation.
    """

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    APP_NAME: str = "FinPilot AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production-must-be-64-chars"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ── Database ───────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://finpilot:finpilot_secret@localhost:5432/finpilot"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # ── Redis ──────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://:redis_secret@localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 20
    REDIS_DECODE_RESPONSES: bool = True

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_AUTH_TOKEN: str = "chroma_secret_token"
    CHROMA_COLLECTION_NAME: str = "finpilot_documents"
    CHROMA_DISTANCE_FUNCTION: str = "cosine"

    # ── JWT ────────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "jwt-dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── AI Models ─────────────────────────────────────────────────────────────
    PRIMARY_LLM_PROVIDER: str = "gemini"  # gemini | groq | openrouter

    # Google Gemini
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_MAX_TOKENS: int = 8192
    GEMINI_TEMPERATURE: float = 0.1

    # Groq
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_MAX_TOKENS: int = 4096

    # OpenRouter (fallback)
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "anthropic/claude-3-haiku"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Embeddings
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    EMBEDDING_DIMENSION: int = 768

    # ── Celery ────────────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://:redis_secret@localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://:redis_secret@localhost:6379/2"
    CELERY_MAX_RETRIES: int = 3
    CELERY_TASK_TIMEOUT: int = 300

    # ── File Storage ──────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: List[str] = [
        "pdf", "docx", "pptx", "xlsx", "csv", "txt",
        "png", "jpg", "jpeg", "tiff"
    ]

    @field_validator("ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def parse_file_types(cls, v):
        if isinstance(v, str):
            return [t.strip() for t in v.split(",")]
        return v

    # ── Document Processing ───────────────────────────────────────────────────
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_CHUNKS_PER_DOCUMENT: int = 500
    OCR_ENABLED: bool = True
    TABLE_EXTRACTION_ENABLED: bool = True

    # ── Email ─────────────────────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "FinPilot AI <noreply@finpilot.ai>"
    SMTP_TLS: bool = True

    # ── OAuth ─────────────────────────────────────────────────────────────────
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = None
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = None
    GOOGLE_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "/app/logs"
    LOG_MAX_SIZE_MB: int = 100
    LOG_BACKUP_COUNT: int = 10

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ── Demo Mode ─────────────────────────────────────────────────────────────
    DEMO_MODE: bool = False
    DEMO_USER_EMAIL: str = "demo@finpilot.ai"
    DEMO_USER_PASSWORD: str = "Demo@FinPilot2024"

    # ── Computed Properties ───────────────────────────────────────────────────

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def upload_dir_path(self) -> str:
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        return self.UPLOAD_DIR

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def active_llm_config(self) -> dict:
        """Returns the configuration for the currently active LLM provider."""
        if self.PRIMARY_LLM_PROVIDER == "gemini" and self.GOOGLE_API_KEY:
            return {
                "provider": "gemini",
                "model": self.GEMINI_MODEL,
                "api_key": self.GOOGLE_API_KEY,
                "max_tokens": self.GEMINI_MAX_TOKENS,
                "temperature": self.GEMINI_TEMPERATURE,
            }
        elif self.PRIMARY_LLM_PROVIDER == "groq" and self.GROQ_API_KEY:
            return {
                "provider": "groq",
                "model": self.GROQ_MODEL,
                "api_key": self.GROQ_API_KEY,
                "max_tokens": self.GROQ_MAX_TOKENS,
                "temperature": 0.1,
            }
        elif self.OPENROUTER_API_KEY:
            return {
                "provider": "openrouter",
                "model": self.OPENROUTER_MODEL,
                "api_key": self.OPENROUTER_API_KEY,
                "max_tokens": 4096,
                "temperature": 0.1,
                "base_url": self.OPENROUTER_BASE_URL,
            }
        else:
            # Fall back to demo mode if no API keys configured
            return {
                "provider": "demo",
                "model": "demo-model",
                "api_key": None,
                "max_tokens": 4096,
                "temperature": 0.1,
            }


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance (singleton pattern)."""
    return Settings()


# Global settings instance
settings = get_settings()
