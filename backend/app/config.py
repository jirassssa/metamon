"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/shadow_trader"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Polymarket API
    polymarket_api_key: str = ""
    polymarket_api_secret: str = ""
    polymarket_api_passphrase: str = ""
    polymarket_host: str = "https://clob.polymarket.com"

    # Application
    app_env: str = "development"
    app_debug: bool = True
    cors_origins: str = "http://localhost:3000"

    # Sentry
    sentry_dsn: str = ""

    # Chain
    chain_id: int = 137

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    def validate_production_settings(self) -> None:
        """Validate settings for production environment."""
        if self.is_production:
            if self.jwt_secret == "change-me-in-production":
                raise ValueError("JWT_SECRET must be changed for production environment")
            if self.app_debug:
                raise ValueError("APP_DEBUG must be false in production environment")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
