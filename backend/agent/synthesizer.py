import os
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv
from backend.models.schemas import SourceResult

load_dotenv()
logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=os.getenv("MOONSHOT_API_KEY"),
    base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1"),
)

MODEL = os.getenv("MOONSHOT_MODEL", "moonshot-v1-128k")

SYNTHESIS_SYSTEM_PROMPT = """You are an expert research analyst. You have been given a research query and a set of web sources gathered to answer it. Your job is to synthesize this into a comprehensive, well-structured research report.

Use EXACTLY this format:

# Research Report: {QUERY_PLACEHOLDER}

## TL;DR
[2-3 sentence summary of the most important findings]

## Key Findings

### [Theme or Sub-question 1]
[Detailed analysis grounded in the provided sources. Cite inline as [Source Title](URL).]

### [Theme or Sub-question 2]
[Continue for each sub-question researched]

## Perspectives & Debates
[Where sources agree, where they conflict, what remains contested]

## Open Questions
[What this research did not fully resolve, what would require deeper investigation]

## Sources
[Numbered list: 1. Title — URL]

## Confidence Level
[High / Medium / Low — one sentence explaining why]

Rules:
- Ground every claim in the provided sources. Do not use knowledge not supported by source content.
- If sources conflict, acknowledge both perspectives.
- Write in clear professional prose. Avoid bullet-point padding.
- Only cite URLs that appear in the provided source list. Never fabricate citations.
- If source content is sparse for a sub-question, say so honestly."""


async def synthesize_report(
    query: str, subquestions: list[str], sources_by_question: dict
) -> str:
    # Build context block from all scraped sources
    context_parts = []
    for i, question in enumerate(subquestions):
        context_parts.append(f"\n\n## Sub-question {i+1}: {question}")
        sources = sources_by_question.get(question, [])
        if not sources:
            context_parts.append("No sources found for this sub-question.")
            continue
        for j, source in enumerate(sources):
            context_parts.append(
                f"\n### Source {j+1}: {source.title}\nURL: {source.url}\n\n{source.snippet}"
            )

    context = "\n".join(context_parts)

    # Inject query into system prompt
    system_prompt = SYNTHESIS_SYSTEM_PROMPT.replace("{QUERY_PLACEHOLDER}", query)

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Research Query: {query}\n\nSources:\n{context}"},
        ],
        temperature=0.5,
        max_tokens=4096,
    )

    return response.choices[0].message.content.strip()
