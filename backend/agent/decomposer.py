import json
import os
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=os.getenv("MOONSHOT_API_KEY"),
    base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1"),
)

MODEL = os.getenv("MOONSHOT_MODEL", "moonshot-v1-128k")

DECOMPOSE_SYSTEM_PROMPT = """You are a research planning assistant. Your job is to decompose a complex research query into a set of specific, answerable sub-questions that together would fully answer the original query.

Rules:
- Each sub-question must be self-contained and directly searchable on the web
- Avoid overlap between sub-questions
- Order them logically — foundational questions first, then specifics
- Return ONLY a valid JSON array of strings. No preamble, no explanation, no markdown fences.

Example output:
["What is X?", "How does X work?", "What are the main use cases of X?"]

Depth guide:
- quick: return 2-3 sub-questions
- standard: return 4-5 sub-questions
- deep: return exactly 6 sub-questions"""


async def decompose_query(query: str, depth: str) -> list[str]:
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": DECOMPOSE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Query: {query}\nDepth: {depth}"},
        ],
        temperature=0.3,
        max_tokens=512,
    )
    raw = response.choices[0].message.content.strip()

    try:
        # Strip markdown fences if model adds them despite instructions
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        subquestions = json.loads(raw)
        if isinstance(subquestions, list) and all(isinstance(q, str) for q in subquestions):
            return subquestions
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: split by newlines and strip numbering
    lines = [line.strip().lstrip("0123456789.-) ") for line in raw.split("\n") if line.strip()]
    return [l for l in lines if len(l) > 5]
