import os

from pydantic import field_validator
from pydantic_settings import BaseSettings


def _fix_database_url(url: str) -> str:
    """Convert Render's postgres:// URL to asyncpg format."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:pass@db:5432/deepresearch"
    redis_url: str = "redis://redis:6379/0"
    moonshot_api_key: str = ""
    firecrawl_api_key: str = ""
    max_concurrent_jobs: int = 5

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        return _fix_database_url(v)

    class Config:
        env_file = ".env"


settings = Settings()
