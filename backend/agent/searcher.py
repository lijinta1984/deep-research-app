import asyncio
import os
import logging
from firecrawl import FirecrawlApp
from backend.models.schemas import SourceResult

logger = logging.getLogger(__name__)


def get_firecrawl_client():
    return FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))


def _sync_search(question: str, max_sources: int) -> list[SourceResult]:
    """Synchronous Firecrawl search — run via asyncio.to_thread to avoid blocking the event loop."""
    app = get_firecrawl_client()

    results = app.search(
        query=question,
        params={
            "limit": max_sources,
            "scrapeOptions": {
                "formats": ["markdown"],
                "onlyMainContent": True,
            },
        },
    )

    # Firecrawl SDK v0.0.16 search() returns response['data'] directly — a list of dicts.
    # Newer versions may return a SearchResponse object with a .data attribute.
    items = results.data if hasattr(results, "data") else results

    sources = []
    for item in items:
        # Handle both dict (v0.0.16) and object (newer SDK) responses
        if isinstance(item, dict):
            url = item.get("url", "") or ""
            title = item.get("title", "") or url
            content = item.get("markdown", "") or item.get("content", "") or ""
        else:
            url = getattr(item, "url", "") or ""
            title = getattr(item, "title", "") or url
            content = getattr(item, "markdown", "") or getattr(item, "content", "") or ""

        if not content:
            continue

        snippet = content[:3000]
        sources.append(
            SourceResult(
                url=url,
                title=title,
                snippet=snippet,
                full_content=content,
            )
        )

    return sources


async def search_and_scrape(question: str, max_sources: int) -> list[SourceResult]:
    try:
        return await asyncio.to_thread(_sync_search, question, max_sources)
    except Exception as e:
        logger.error(f"Firecrawl search failed for '{question}': {e}")
        return []  # Never crash the orchestrator — return empty list and continue
