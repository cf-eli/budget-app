"""Configuration settings for the finance API."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    test_jwt_aud: str = "test-dev"
    jwt_algorithm: str = "HS256"
    enable_auth: bool = True
    db_host: str = "localhost"
    finance_db_name: str = "finance"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"  # noqa: S105
    homelab_client_secret: str = ""
    finance_jwt_aud: str = "finance-api"
    # Default user for development when auth is disabled
    dev_default_user_id: str = "user_001"


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()


settings = get_settings()
