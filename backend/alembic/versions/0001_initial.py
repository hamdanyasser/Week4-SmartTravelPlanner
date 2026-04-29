"""Initial AtlasBrief schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-29

Creates the six tables the app reads/writes today: users, agent_runs,
tool_calls, webhook_deliveries, destination_documents, document_chunks.
The pgvector extension is enabled before the embedding column is created
so this migration also works as a fresh-bootstrap step on a new database.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True, index=True),
        sa.Column("display_name", sa.String(120), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="started", index=True),
        sa.Column("response_json", sa.JSON, nullable=True),
        sa.Column("tokens_in", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default="0"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "tool_calls",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "agent_run_id",
            sa.Integer,
            sa.ForeignKey("agent_runs.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("tool_name", sa.String(120), nullable=False, index=True),
        sa.Column("status", sa.String(40), nullable=False, index=True),
        sa.Column("input_json", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("output_json", sa.JSON, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("tokens_in", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "agent_run_id",
            sa.Integer,
            sa.ForeignKey("agent_runs.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("channel", sa.String(80), nullable=False, server_default="discord"),
        sa.Column("status", sa.String(40), nullable=False, index=True),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("response_status_code", sa.Integer, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "destination_documents",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("destination", sa.String(120), nullable=False, index=True),
        sa.Column("source_title", sa.String(240), nullable=False),
        sa.Column("source_type", sa.String(80), nullable=False, index=True),
        sa.Column("source_path", sa.String(500), nullable=False, unique=True),
        sa.Column("content_hash", sa.String(64), nullable=False, index=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "document_id",
            sa.Integer,
            sa.ForeignKey("destination_documents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("destination", sa.String(120), nullable=False, index=True),
        sa.Column("source_title", sa.String(240), nullable=False),
        sa.Column("source_type", sa.String(80), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_document_chunks_embedding_cosine",
        "document_chunks",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_with={"lists": 100},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_document_chunks_embedding_cosine", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_table("destination_documents")
    op.drop_table("webhook_deliveries")
    op.drop_table("tool_calls")
    op.drop_table("agent_runs")
    op.drop_table("users")
