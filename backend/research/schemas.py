from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid

ConfidenceLevel = Literal["high", "medium", "low"]
Priority        = Literal["high", "medium", "low"]
ResearchDepth   = Literal[1, 2, 3]
JobStatus       = Literal["queued", "running", "complete", "failed"]

# ── Pass 1 ──────────────────────────────────────────────────────────

class KeyFinding(BaseModel):
    claim: str
    confidence: ConfidenceLevel
    source_urls: list[str] = Field(default_factory=list)

class KeyFindingWithMeta(KeyFinding):
    is_new: bool = False
    resolves_gap: Optional[str] = None

class Contradiction(BaseModel):
    point: str
    source_a: str
    source_b: str
    resolved: bool = False
    resolution: Optional[str] = None

class KnowledgeGap(BaseModel):
    question: str
    priority: Priority
    reason: str

class Pass1Synthesis(BaseModel):
    overview: str
    key_findings: list[KeyFinding]
    themes: list[str]
    contradictions: list[Contradiction]

class Pass1Output(BaseModel):
    synthesis: Pass1Synthesis
    gaps: list[KnowledgeGap]
    pass_complete: bool = True

# ── Pass 2 ──────────────────────────────────────────────────────────

class ResolvedGap(BaseModel):
    question: str
    resolution_summary: str
    confidence: ConfidenceLevel

class Pass2Synthesis(BaseModel):
    overview: str
    key_findings: list[KeyFindingWithMeta]
    themes: list[str]
    contradictions: list[Contradiction]

class Pass2Output(BaseModel):
    updated_synthesis: Pass2Synthesis
    gaps_resolved: list[ResolvedGap]
    remaining_gaps: list[KnowledgeGap]
    pass_complete: bool = True

# ── Pass 3 ──────────────────────────────────────────────────────────

class ReportSection(BaseModel):
    title: str
    content: str
    confidence: ConfidenceLevel
    confidence_rationale: str

class KeyConclusion(BaseModel):
    conclusion: str
    confidence: ConfidenceLevel

class OpenQuestion(BaseModel):
    question: str
    why_it_matters: str

class SourceRecord(BaseModel):
    url: str
    title: str
    relevance: ConfidenceLevel
    found_in_pass: Literal[1, 2, 3]

class ResearchMetadata(BaseModel):
    total_passes: int
    total_sources_scraped: int
    total_gaps_identified: int
    total_gaps_resolved: int
    research_confidence_overall: ConfidenceLevel

class FinalReport(BaseModel):
    executive_summary: str
    sections: list[ReportSection]
    key_conclusions: list[KeyConclusion]
    open_questions: list[OpenQuestion]

class Pass3Output(BaseModel):
    report: FinalReport
    sources: list[SourceRecord]
    metadata: ResearchMetadata
    pass_complete: bool = True

# ── Job lifecycle ────────────────────────────────────────────────────

class ResearchJobCreate(BaseModel):
    query: str = Field(..., min_length=5, max_length=500)
    depth: ResearchDepth = 2
    max_sources: int = Field(default=10, ge=5, le=20)

class ResearchJobResponse(BaseModel):
    job_id: str
    query: str
    depth: ResearchDepth
    max_sources: int
    status: JobStatus
    created_at: datetime

class ResearchProgress(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = Field(..., ge=0, le=100)
    current_pass: int = Field(..., ge=0, le=3)
    sources_scraped: int = 0
    gaps_found: int = 0
    partial_synthesis: Optional[str] = None
    error_message: Optional[str] = None

class ScrapedSource(BaseModel):
    url: str
    title: str
    markdown_content: str
    scraped_at: datetime
    pass_number: Literal[1, 2, 3]
    word_count: int
    scrape_success: bool

class ResearchJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    depth: ResearchDepth
    max_sources: int
    status: JobStatus = "queued"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    sources: list[ScrapedSource] = Field(default_factory=list)
    pass_1_output: Optional[Pass1Output] = None
    pass_2_output: Optional[Pass2Output] = None
    pass_3_output: Optional[Pass3Output] = None
    error_message: Optional[str] = None

class SearchTreeNode(BaseModel):
    id: str
    label: str
    node_type: Literal["root", "query", "gap", "source"]
    pass_number: Literal[1, 2, 3]
    parent_id: Optional[str] = None
    url: Optional[str] = None
    confidence: Optional[ConfidenceLevel] = None
    children: list["SearchTreeNode"] = Field(default_factory=list)

SearchTreeNode.model_rebuild()

class ExportRequest(BaseModel):
    job_id: str
    format: Literal["docx", "markdown"] = "docx"
    include_sources: bool = True
    include_open_questions: bool = True
