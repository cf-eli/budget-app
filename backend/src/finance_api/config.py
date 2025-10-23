from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    test_jwt_aud: str = "test-dev"
    jwt_algorithm: str = "HS256"
    enable_auth: bool = True
    db_host: str = "localhost"
    finance_db_name: str = "finance"
    db_port: int = 5432
    db_user: str = "admin"
    db_password: str  = "admin"
    homelab_client_secret: str = ""
    finance_jwt_aud: str = "finance-api"

    class Config:
        env_file = ".env"
        extra = "ignore"


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
