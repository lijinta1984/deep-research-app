import asyncio
import logging
from backend.agent.decomposer import decompose_query
from backend.agent.searcher import search_and_scrape
from backend.agent.synthesizer import synthesize_report
from backend.db.database import save_session
from backend.models.schemas import ResearchRequest, ResearchStep, SourceResult

logger = logging.getLogger(__name__)

DEPTH_CONFIG = {
    "quick": {"max_subquestions": 3, "max_sources": 2},
    "standard": {"max_subquestions": 5, "max_sources": 3},
    "deep": {"max_subquestions": 6, "max_sources": 4},
}


async def run_research(
    request: ResearchRequest, session_id: str, queue: asyncio.Queue
):
    config = DEPTH_CONFIG.get(request.depth, DEPTH_CONFIG["standard"])
    sources_by_question: dict[str, list[SourceResult]] = {}
    all_sources: list[SourceResult] = []

    try:
        # --- Step 1: Decompose query ---
        await queue.put(
            ResearchStep(
                type="decompose",
                message="Breaking your query into focused sub-questions...",
            )
        )

        subquestions = await decompose_query(request.query, request.depth)
        subquestions = subquestions[: config["max_subquestions"]]

        await queue.put(
            ResearchStep(
                type="decompose",
                message=f"Identified {len(subquestions)} research angles",
                data={"subquestions": subquestions},
            )
        )

        # --- Step 2: Search + scrape each sub-question ---
        for i, question in enumerate(subquestions):
            await queue.put(
                ResearchStep(
                    type="search",
                    message=f"Searching ({i+1}/{len(subquestions)}): {question}",
                    data={"question_index": i, "question": question},
                )
            )

            sources = await search_and_scrape(question, config["max_sources"])
            sources_by_question[question] = sources
            all_sources.extend(sources)

            await queue.put(
                ResearchStep(
                    type="scrape",
                    message=f"Found {len(sources)} source(s) for sub-question {i+1}",
                    data={
                        "question_index": i,
                        "sources": [
                            {"url": s.url, "title": s.title} for s in sources
                        ],
                    },
                )
            )

            # Rate-limit protection: brief pause between Firecrawl calls
            await asyncio.sleep(0.8)

        # --- Step 3: Synthesize ---
        await queue.put(
            ResearchStep(
                type="synthesize",
                message="Synthesizing findings into a structured report via Kimi K2...",
            )
        )

        report = await synthesize_report(
            request.query, subquestions, sources_by_question
        )

        # --- Step 4: Persist session ---
        await asyncio.to_thread(
            save_session,
            session_id,
            request.query,
            request.depth,
            "complete",
            report,
            all_sources,
        )

        # --- Step 5: Signal completion ---
        await queue.put(
            ResearchStep(
                type="complete",
                message="Research complete",
                data={
                    "report": report,
                    "sources": [s.model_dump() for s in all_sources],
                    "session_id": session_id,
                },
            )
        )

    except Exception as e:
        logger.error(
            f"Orchestrator failed for session {session_id}: {e}", exc_info=True
        )
        try:
            await asyncio.to_thread(
                save_session, session_id, request.query, request.depth, "failed", "", []
            )
        except Exception as save_err:
            logger.error(f"Failed to persist failed session {session_id}: {save_err}")
        await queue.put(
            ResearchStep(type="error", message=f"Research failed: {str(e)}")
        )
