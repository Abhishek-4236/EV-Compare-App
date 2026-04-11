"""add knowledge_articles table

Revision ID: 20260411_01
Revises: 20260410_01
Create Date: 2026-04-11 10:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260411_01"
down_revision: Union[str, Sequence[str], None] = "20260410_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_articles",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "embedding",
            postgresql.VECTOR(dim=384),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_knowledge_articles_id", "knowledge_articles", ["id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_articles_id", table_name="knowledge_articles")
    op.drop_table("knowledge_articles")
