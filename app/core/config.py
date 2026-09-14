"""
Application configuration using Pydantic Settings.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "FlyRank Widget Platform"
    DEBUG: bool = False

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
