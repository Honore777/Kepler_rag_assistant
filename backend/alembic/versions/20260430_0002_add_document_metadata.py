"""add document_metadata table

Revision ID: 20260430_0002
Revises: 20260422_0001
Create Date: 2026-04-30 00:02:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260430_0002"
down_revision = "20260422_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doc_id", sa.String(length=255), nullable=False),
        sa.Column("doc_name", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=False, server_default="policy"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("allowed_roles", sa.Text(), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("version", sa.String(length=20), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("file_type", sa.String(length=10), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "document_type IN ('policy', 'research', 'handbook', 'procedure', 'other')",
            name="ck_document_type",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'archived')",
            name="ck_document_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doc_id"),
    )
    op.create_index("ix_document_metadata_doc_id", "document_metadata", ["doc_id"], unique=False)
    op.create_index("ix_document_metadata_document_type", "document_metadata", ["document_type"], unique=False)
    op.create_index("ix_document_metadata_department", "document_metadata", ["department"], unique=False)
    op.create_index("ix_document_metadata_status", "document_metadata", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_document_metadata_status", table_name="document_metadata")
    op.drop_index("ix_document_metadata_department", table_name="document_metadata")
    op.drop_index("ix_document_metadata_document_type", table_name="document_metadata")
    op.drop_index("ix_document_metadata_doc_id", table_name="document_metadata")
    op.drop_table("document_metadata")
