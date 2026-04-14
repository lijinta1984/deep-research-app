"""initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "research_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column("max_sources", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_pass", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sources_scraped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("gaps_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("partial_synthesis", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sources_json", postgresql.JSONB(), nullable=True),
        sa.Column("pass_1_output_json", postgresql.JSONB(), nullable=True),
        sa.Column("pass_2_output_json", postgresql.JSONB(), nullable=True),
        sa.Column("pass_3_output_json", postgresql.JSONB(), nullable=True),
        sa.Column("search_tree_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_research_jobs_job_id", "research_jobs", ["job_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_research_jobs_job_id", table_name="research_jobs")
    op.drop_table("research_jobs")
