import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.api.routes import router as research_router
from backend.db.session import engine, Base

# Configure loguru
logger.remove()
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO",
    serialize=True,
)

app = FastAPI(
    title="Deep Research API",
    description="Production-grade deep research engine powered by Kimi K2 + Firecrawl",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router)


@app.on_event("startup")
async def startup() -> None:
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created / verified")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
