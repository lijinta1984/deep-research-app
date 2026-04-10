import json
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.models.schemas import SourceResult
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./research_sessions.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ResearchSessionRow(Base):
    __tablename__ = "research_sessions"

    id = Column(String, primary_key=True)
    query = Column(Text, nullable=False)
    depth = Column(String, nullable=False)
    status = Column(String, nullable=False)
    report = Column(Text, nullable=True)
    sources_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    Base.metadata.create_all(bind=engine)


def save_session(id: str, query: str, depth: str, status: str, report: str, sources: list[SourceResult]):
    db = SessionLocal()
    try:
        existing = db.query(ResearchSessionRow).filter_by(id=id).first()
        sources_data = json.dumps([s.model_dump() for s in sources])
        if existing:
            existing.query = query
            existing.depth = depth
            existing.status = status
            existing.report = report
            existing.sources_json = sources_data
        else:
            row = ResearchSessionRow(
                id=id,
                query=query,
                depth=depth,
                status=status,
                report=report,
                sources_json=sources_data,
                created_at=datetime.now(timezone.utc),
            )
            db.add(row)
        db.commit()
    finally:
        db.close()


def get_session(id: str) -> dict:
    db = SessionLocal()
    try:
        row = db.query(ResearchSessionRow).filter_by(id=id).first()
        if not row:
            return {}
        return {
            "id": row.id,
            "query": row.query,
            "depth": row.depth,
            "status": row.status,
            "report": row.report,
            "sources_json": row.sources_json or "[]",
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
    finally:
        db.close()


def list_sessions(limit: int = 20) -> list[dict]:
    db = SessionLocal()
    try:
        rows = (
            db.query(ResearchSessionRow)
            .order_by(ResearchSessionRow.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "query": r.query,
                "depth": r.depth,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    finally:
        db.close()


def delete_session(id: str):
    db = SessionLocal()
    try:
        row = db.query(ResearchSessionRow).filter_by(id=id).first()
        if row:
            db.delete(row)
            db.commit()
    finally:
        db.close()
