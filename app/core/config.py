"""
Application configuration using Pydantic Settings.
Phase 2: Updated with CORS and rate limiting config.
"""
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "FlyRank Widget Platform"
    DEBUG: bool = False
    API_BASE_URL: str = "http://localhost:8000"

    # Database
    DATABASE_URL: str = Field(
        ..., description="MySQL connection string"
    )

    # JWT
    JWT_SECRET_KEY: str = Field(
        ..., description="Secret key for JWT signing"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5500"],
        description="Allowed CORS origins"
    )

    # Rate Limiting
    RATE_LIMIT_MAX_REQUESTS: int = Field(
        default=10,
        description="Maximum requests per window"
    )
    RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=60,
        description="Rate limit window in seconds"
    )

    # Submission
    MAX_SUBMISSION_PAYLOAD_SIZE: int = Field(
        default=65536,  # 64KB
        description="Maximum submission payload size in bytes"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
