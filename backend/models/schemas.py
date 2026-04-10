from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ResearchRequest(BaseModel):
    query: str
    depth: str = "standard"          # "quick" | "standard" | "deep"


class SubQuestion(BaseModel):
    id: int
    question: str
    status: str = "pending"          # pending | searching | done | failed


class SourceResult(BaseModel):
    url: str
    title: str
    snippet: str                     # First 3000 chars of scraped content
    full_content: str                # Full scraped markdown


class ResearchStep(BaseModel):
    type: str                        # "decompose" | "search" | "scrape" | "synthesize" | "complete" | "error" | "ping"
    message: str
    data: dict = {}


class ResearchSession(BaseModel):
    id: str
    query: str
    depth: str
    status: str                      # running | complete | failed
    report: str = ""
    sources: list[SourceResult] = []
    created_at: datetime
