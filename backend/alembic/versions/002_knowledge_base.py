"""Knowledge base schema

Revision ID: 002
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_spaces",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("metadata", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_knowledge_spaces_user_id", "knowledge_spaces", ["user_id"])

    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("space_id", sa.UUID(), sa.ForeignKey("knowledge_spaces.id", ondelete="CASCADE")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("config", sa.JSON(), server_default="{}"),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("watch_enabled", sa.Boolean(), server_default="true"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("sync_cursor", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_knowledge_sources_space_id", "knowledge_sources", ["space_id"])

    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("space_id", sa.UUID(), sa.ForeignKey("knowledge_spaces.id", ondelete="CASCADE")),
        sa.Column("source_id", sa.UUID(), sa.ForeignKey("knowledge_sources.id", ondelete="SET NULL")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("file_size", sa.Integer(), server_default="0"),
        sa.Column("chunk_count", sa.Integer(), server_default="0"),
        sa.Column("metadata", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_documents_space_id", "documents", ["space_id"])
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"])
    op.create_index("idx_documents_space_path", "documents", ["space_id", "file_path"], unique=True)

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("document_id", sa.UUID(), sa.ForeignKey("documents.id", ondelete="CASCADE")),
        sa.Column("space_id", sa.UUID(), sa.ForeignKey("knowledge_spaces.id", ondelete="CASCADE")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("chunk_index", sa.Integer(), server_default="0"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(384)),
        sa.Column("search_vector", sa.dialects.postgresql.TSVECTOR()),
        sa.Column("metadata", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_space_id", "document_chunks", ["space_id"])
    op.create_index("idx_chunks_space_doc", "document_chunks", ["space_id", "document_id"])

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("space_id", sa.UUID(), sa.ForeignKey("knowledge_spaces.id", ondelete="CASCADE")),
        sa.Column("source_id", sa.UUID(), sa.ForeignKey("knowledge_sources.id", ondelete="SET NULL")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("progress", sa.Float(), server_default="0"),
        sa.Column("files_processed", sa.Integer(), server_default="0"),
        sa.Column("chunks_created", sa.Integer(), server_default="0"),
        sa.Column("error", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("ingestion_jobs")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("knowledge_sources")
    op.drop_table("knowledge_spaces")
