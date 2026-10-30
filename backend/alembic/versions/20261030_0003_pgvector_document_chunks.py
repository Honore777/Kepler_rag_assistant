"""pgvector document_chunks table + document_metadata indexing columns

Replaces the Chroma-on-disk vector store with pgvector in Postgres, and moves
the JSON file manifest into document_metadata so nothing lives on the
container filesystem.

Revision ID: 20261030_0003
Revises: 20260430_0002
Create Date: 2026-10-30 00:03:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

from app.core.config import settings

# revision identifiers, used by Alembic.
revision = "20261030_0003"
down_revision = "20260430_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(length=320), nullable=False),
        sa.Column("doc_id", sa.String(length=255), nullable=False),
        sa.Column("doc_name", sa.String(length=255), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(settings.EMBEDDING_DIM), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("allowed_roles", sa.Text(), nullable=True),
        sa.Column("document_type", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_chunks_doc_id", "document_chunks", ["doc_id"], unique=False)
    # HNSW index for fast approximate cosine-similarity search.
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding_hnsw "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops)"
    )

    # Manifest columns on document_metadata (replaces documents_manifest.json)
    op.add_column("document_metadata", sa.Column("file_path", sa.Text(), nullable=True))
    op.add_column(
        "document_metadata",
        sa.Column("storage_backend", sa.String(length=20), nullable=False, server_default="local"),
    )
    op.add_column("document_metadata", sa.Column("storage_object_name", sa.Text(), nullable=True))
    op.add_column(
        "document_metadata",
        sa.Column("indexing_state", sa.String(length=20), nullable=False, server_default="queued"),
    )
    op.add_column("document_metadata", sa.Column("indexing_message", sa.Text(), nullable=True))
    op.add_column("document_metadata", sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True))

    # Script-indexed documents have no uploader user id.
    op.alter_column("document_metadata", "uploaded_by", existing_type=postgresql.UUID(as_uuid=True), nullable=True)


def downgrade() -> None:
    op.alter_column("document_metadata", "uploaded_by", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.drop_column("document_metadata", "indexed_at")
    op.drop_column("document_metadata", "indexing_message")
    op.drop_column("document_metadata", "indexing_state")
    op.drop_column("document_metadata", "storage_object_name")
    op.drop_column("document_metadata", "storage_backend")
    op.drop_column("document_metadata", "file_path")

    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    op.drop_index("ix_document_chunks_doc_id", table_name="document_chunks")
    op.drop_table("document_chunks")
