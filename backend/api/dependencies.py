import os

from pydantic_settings import BaseSettings


def _fix_database_url(url: str) -> str:
    """Convert Render's postgres:// URL to asyncpg format."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


class Settings(BaseSettings):
    database_url: str = _fix_database_url(
        os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://user:pass@db:5432/deepresearch",
        )
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    moonshot_api_key: str = os.getenv("MOONSHOT_API_KEY", "")
    firecrawl_api_key: str = os.getenv("FIRECRAWL_API_KEY", "")
    max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))

    class Config:
        env_file = ".env"


settings = Settings()
