import asyncio
from datetime import datetime
from typing import Any

from celery import Celery
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.api.dependencies import settings
from backend.db.models import ResearchJobModel
from backend.research.engine import ResearchEngine

celery_app = Celery("deep_research", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=settings.max_concurrent_jobs,
    task_soft_time_limit=540,
    task_time_limit=600,
)


def _run_async(coro):  # type: ignore[no-untyped-def]
    """Run an async coroutine in a new event loop (for Celery sync workers)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _update_job_field(job_id: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
    """Update specific fields on a research job in the database.

    Creates a fresh async engine per call to avoid event-loop mismatch
    when running inside Celery's sync workers via _run_async().
    """
    _engine = create_async_engine(settings.database_url, echo=False)
    _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with _session_factory() as session:
            stmt = select(ResearchJobModel).where(ResearchJobModel.job_id == job_id)
            result = await session.execute(stmt)
            job = result.scalar_one_or_none()
            if job is None:
                return
            for key, value in kwargs.items():
                setattr(job, key, value)
            await session.commit()
    finally:
        await _engine.dispose()


@celery_app.task(name="run_research", bind=True, max_retries=0)
def run_research_task(self, job_id: str, query: str, depth: int, max_sources: int) -> None:  # type: ignore[no-untyped-def]
    """Execute the multi-pass research pipeline as a Celery task."""
    logger.info("Starting research task for job_id={}", job_id)

    try:
        _run_async(
            _update_job_field(job_id, status="running")
        )

        async def _progress_cb(**kwargs: Any) -> None:
            """Async callback invoked by the engine to report incremental progress."""
            await _update_job_field(job_id, **kwargs)

        engine = ResearchEngine(progress_callback=_progress_cb)
        results = _run_async(
            engine.run(query=query, depth=depth, max_sources=max_sources)
        )

        pass_1 = results["pass_1_output"]
        pass_2 = results.get("pass_2_output")
        pass_3 = results["pass_3_output"]
        sources = results["sources"]
        tree = results["tree"]

        sources_json = [s.model_dump(mode="json") for s in sources]
        total_scraped = sum(1 for s in sources if s.scrape_success)
        gaps_found = len(pass_1.gaps) if pass_1 else 0

        update_kwargs = {
            "status": "complete",
            "progress": 100,
            "current_pass": 3,
            "sources_scraped": total_scraped,
            "gaps_found": gaps_found,
            "sources_json": sources_json,
            "pass_1_output_json": pass_1.model_dump(mode="json"),
            "pass_3_output_json": pass_3.model_dump(mode="json"),
            "search_tree_json": tree.model_dump(mode="json"),
            "completed_at": datetime.utcnow(),
        }

        if pass_1 and pass_1.synthesis:
            update_kwargs["partial_synthesis"] = pass_1.synthesis.overview

        if pass_2:
            update_kwargs["pass_2_output_json"] = pass_2.model_dump(mode="json")

        _run_async(_update_job_field(job_id, **update_kwargs))
        logger.info("Research task completed for job_id={}", job_id)

    except Exception as exc:
        logger.error("Research task failed for job_id={}: {}", job_id, exc)
        try:
            _run_async(
                _update_job_field(
                    job_id,
                    status="failed",
                    error_message=str(exc),
                )
            )
        except Exception as db_exc:
            logger.error("Failed to update job status for job_id={}: {}", job_id, db_exc)
        raise
