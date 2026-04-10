import os
import logging
from firecrawl import FirecrawlApp
from backend.models.schemas import SourceResult

logger = logging.getLogger(__name__)


def get_firecrawl_client():
    return FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))


async def search_and_scrape(question: str, max_sources: int) -> list[SourceResult]:
    try:
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

        sources = []
        for item in results.data:
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

    except Exception as e:
        logger.error(f"Firecrawl search failed for '{question}': {e}")
        return []  # Never crash the orchestrator — return empty list and continue
