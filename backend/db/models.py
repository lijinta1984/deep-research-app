import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.session import Base


class ResearchJobModel(Base):
    __tablename__ = "research_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    max_sources: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_pass: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sources_scraped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gaps_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partial_synthesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pass_1_output_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pass_2_output_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pass_3_output_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    search_tree_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
