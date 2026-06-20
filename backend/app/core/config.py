"""
Central app configuration. Secrets are read from environment variables —
never hardcoded. Generate SECRET_KEY with: openssl rand -hex 32
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "CivicFlow AI"
    ENV: str = "development"

    # Database
    DATABASE_URL: str = "sqlite:///./civicflow.db"

    # JWT / Auth security
    SECRET_KEY: str = "CHANGE_ME_GENERATE_WITH_openssl_rand_hex_32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://civicflow.vercel.app",
    ]

    # Rate limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    class Config:
        env_file = ".env"

    @property
    def is_production(self) -> bool:
        return self.ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
