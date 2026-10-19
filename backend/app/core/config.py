# backend/app/core/config.py
"""
Centralized application configuration via Pydantic Settings.

Every environment variable the backend reads is declared here —
nowhere else in the codebase should call os.environ[...] or
os.getenv(...) directly. This is what backend/.env.example (generated
alongside this) documents, and what main.py, db/mongo_client.py,
auth/jwt_handler.py, ai/gemini/gemini_client.py, integrations/gmail/*,
and every service module import via get_settings().
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --------------------------------------------------------------------
    # App metadata
    # --------------------------------------------------------------------
    APP_NAME: str = "AI Email OS API"
    ENVIRONMENT: str = Field(default="development")  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"

    # --------------------------------------------------------------------
    # Server
    # --------------------------------------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --------------------------------------------------------------------
    # CORS — comma-separated origins in .env, parsed into a list
    # --------------------------------------------------------------------
    CORS_ALLOWED_ORIGINS_RAW: str = Field(
        default="http://localhost:5173",
        alias="CORS_ALLOWED_ORIGINS",
    )

    @property
    def CORS_ALLOWED_ORIGINS(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS_RAW.split(",") if origin.strip()]

    # --------------------------------------------------------------------
    # MongoDB Atlas (Motor async client — see db/mongo_client.py)
    # --------------------------------------------------------------------
    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017",
        description="Full MongoDB Atlas connection string, including credentials.",
    )
    MONGODB_DB_NAME: str = "ai_email_os"

    # --------------------------------------------------------------------
    # JWT Authentication (see core/security.py, auth/jwt_handler.py)
    # --------------------------------------------------------------------
    JWT_SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        description="Symmetric signing key for access/refresh tokens. MUST be overridden in production.",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --------------------------------------------------------------------
    # Google OAuth 2.0 (see integrations/google_oauth/oauth_client.py)
    # --------------------------------------------------------------------
    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")
    GOOGLE_OAUTH_REDIRECT_URI: str = Field(default="http://localhost:8000/api/v1/auth/google/callback")

    GOOGLE_OAUTH_SCOPES_RAW: str = Field(
        default=(
            "openid email profile "
            "https://www.googleapis.com/auth/gmail.readonly "
            "https://www.googleapis.com/auth/gmail.send "
            "https://www.googleapis.com/auth/gmail.modify "
            "https://www.googleapis.com/auth/calendar"
        ),
        alias="GOOGLE_OAUTH_SCOPES",
    )

    @property
    def GOOGLE_OAUTH_SCOPES(self) -> List[str]:
        return self.GOOGLE_OAUTH_SCOPES_RAW.split()

    # Where the frontend lives, for post-login/error redirects
    FRONTEND_BASE_URL: str = Field(default="http://localhost:5173")

    # --------------------------------------------------------------------
    # Google Gemini (AI layer — see ai/gemini/gemini_client.py)
    # --------------------------------------------------------------------
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash")
    GEMINI_MAX_OUTPUT_TOKENS: int = 2048
    GEMINI_TEMPERATURE: float = 0.4

    # --------------------------------------------------------------------
    # ChromaDB (vector store — see ai/rag/vectorstore/chroma_client.py)
    # --------------------------------------------------------------------
    CHROMA_PERSIST_DIR: str = Field(default="./chroma_data")
    CHROMA_COLLECTION_NAME: str = Field(default="email_embeddings")
    # Optional: point at a remote Chroma server instead of embedded/local mode
    CHROMA_SERVER_HOST: str = Field(default="")
    CHROMA_SERVER_PORT: int = Field(default=8001)

    # --------------------------------------------------------------------
    # Rate limiting (see middlewares/rate_limiter.py)
    # --------------------------------------------------------------------
    RATE_LIMIT_PER_MINUTE: int = 120

    # --------------------------------------------------------------------
    # Background scheduler (see tasks/scheduler.py)
    # --------------------------------------------------------------------
    INBOX_SYNC_INTERVAL_MINUTES: int = 5
    DAILY_BRIEF_HOUR_UTC: int = 6  # hour of day (UTC) to generate daily briefs

    # --------------------------------------------------------------------
    # Misc / derived
    # --------------------------------------------------------------------
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor. lru_cache ensures .env is parsed exactly
    once per process, not on every call — every module that needs
    config calls `get_settings()` rather than instantiating Settings()
    directly, so the cache is actually shared.
    """
    return Settings()