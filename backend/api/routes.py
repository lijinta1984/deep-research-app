import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import ResearchJobModel
from backend.db.session import get_session
from backend.export.docx_builder import build_docx, build_markdown
from backend.research.schemas import (
    ExportRequest,
    Pass1Output,
    Pass2Output,
    Pass3Output,
    ResearchJob,
    ResearchJobCreate,
    ResearchJobResponse,
    ResearchProgress,
    ScrapedSource,
    SearchTreeNode,
)
from backend.tasks.celery_tasks import run_research_task

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("/start", response_model=ResearchJobResponse)
async def start_research(
    body: ResearchJobCreate,
    session: AsyncSession = Depends(get_session),
) -> ResearchJobResponse:
    """Create a new research job and enqueue it."""
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()

    db_job = ResearchJobModel(
        job_id=job_id,
        query=body.query,
        depth=body.depth,
        max_sources=body.max_sources,
        status="queued",
        progress=0,
        current_pass=0,
        created_at=now,
    )
    session.add(db_job)
    await session.commit()

    run_research_task.delay(job_id, body.query, body.depth, body.max_sources)
    logger.info("Research job {} enqueued for query: {}", job_id, body.query)

    return ResearchJobResponse(
        job_id=job_id,
        query=body.query,
        depth=body.depth,
        max_sources=body.max_sources,
        status="queued",
        created_at=now,
    )


@router.get("/status/{job_id}", response_model=ResearchProgress)
async def get_status(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> ResearchProgress:
    """Get progress for a research job (poll-friendly)."""
    stmt = select(ResearchJobModel).where(
        ResearchJobModel.job_id == job_id,
        ResearchJobModel.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return ResearchProgress(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        current_pass=job.current_pass,
        sources_scraped=job.sources_scraped,
        gaps_found=job.gaps_found,
        partial_synthesis=job.partial_synthesis,
        error_message=job.error_message,
    )


@router.get("/result/{job_id}", response_model=ResearchJob)
async def get_result(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> ResearchJob:
    """Get the full result of a completed research job."""
    stmt = select(ResearchJobModel).where(
        ResearchJobModel.job_id == job_id,
        ResearchJobModel.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    sources: list[ScrapedSource] = []
    if job.sources_json:
        sources = [ScrapedSource.model_validate(s) for s in job.sources_json]

    return ResearchJob(
        job_id=job.job_id,
        query=job.query,
        depth=job.depth,
        max_sources=job.max_sources,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        sources=sources,
        pass_1_output=(
            Pass1Output.model_validate(job.pass_1_output_json)
            if job.pass_1_output_json
            else None
        ),
        pass_2_output=(
            Pass2Output.model_validate(job.pass_2_output_json)
            if job.pass_2_output_json
            else None
        ),
        pass_3_output=(
            Pass3Output.model_validate(job.pass_3_output_json)
            if job.pass_3_output_json
            else None
        ),
        error_message=job.error_message,
    )


@router.get("/history", response_model=list[ResearchJobResponse])
async def get_history(
    session: AsyncSession = Depends(get_session),
) -> list[ResearchJobResponse]:
    """Get recent research jobs ordered by creation date."""
    stmt = (
        select(ResearchJobModel)
        .where(ResearchJobModel.deleted_at.is_(None))
        .order_by(ResearchJobModel.created_at.desc())
        .limit(50)
    )
    result = await session.execute(stmt)
    jobs = result.scalars().all()

    return [
        ResearchJobResponse(
            job_id=j.job_id,
            query=j.query,
            depth=j.depth,
            max_sources=j.max_sources,
            status=j.status,
            created_at=j.created_at,
        )
        for j in jobs
    ]


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Soft delete a research job."""
    stmt = select(ResearchJobModel).where(
        ResearchJobModel.job_id == job_id,
        ResearchJobModel.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    job.deleted_at = datetime.utcnow()
    await session.commit()
    return {"status": "deleted"}


@router.post("/export/{job_id}")
async def export_report(
    job_id: str,
    body: ExportRequest,
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """Export a completed research report as DOCX or Markdown."""
    stmt = select(ResearchJobModel).where(
        ResearchJobModel.job_id == job_id,
        ResearchJobModel.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.pass_3_output_json:
        raise HTTPException(status_code=400, detail="Research not yet complete")

    pass_3 = Pass3Output.model_validate(job.pass_3_output_json)

    if body.format == "docx":
        buffer = build_docx(
            query=job.query,
            depth=job.depth,
            pass_3=pass_3,
            include_sources=body.include_sources,
            include_open_questions=body.include_open_questions,
        )
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="research_{job_id[:8]}.docx"'
            },
        )
    else:
        md_content = build_markdown(
            query=job.query,
            depth=job.depth,
            pass_3=pass_3,
            include_sources=body.include_sources,
            include_open_questions=body.include_open_questions,
        )
        return StreamingResponse(
            iter([md_content.encode()]),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="research_{job_id[:8]}.md"'
            },
        )


@router.get("/tree/{job_id}", response_model=SearchTreeNode)
async def get_search_tree(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> SearchTreeNode:
    """Get the search tree visualization data for a research job."""
    stmt = select(ResearchJobModel).where(
        ResearchJobModel.job_id == job_id,
        ResearchJobModel.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.search_tree_json:
        raise HTTPException(status_code=400, detail="Search tree not yet available")

    return SearchTreeNode.model_validate(job.search_tree_json)
