"""ORM models used by Alembic migrations and runtime services."""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.db.base import Base


class User(Base):
    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint("role IN ('student', 'admin', 'staff', 'board_member')", name="ck_user_role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False, default="student")
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    program: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="active", index=True)
    profile_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class DocumentMetadata(Base):
    """Document metadata for role-based access control."""
    __tablename__ = "document_metadata"
    __table_args__ = (
        CheckConstraint("document_type IN ('policy', 'research', 'handbook', 'procedure', 'other')", name="ck_document_type"),
        CheckConstraint("status IN ('active', 'inactive', 'archived')", name="ck_document_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    doc_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 🔥 Document classification
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, default="policy", index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 🔥 Access control
    allowed_roles: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of roles
    department: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    
    # 🔥 Lifecycle
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expires_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 🔥 Metadata
    file_size: Mapped[int] = mapped_column(nullable=True)
    file_type: Mapped[str] = mapped_column(String(10), nullable=True)
    # Nullable so scripts (e.g. index_existing.py) can register documents
    # without an uploader user id.
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # 🔥 Storage + indexing lifecycle (replaces the old on-disk JSON manifest)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_backend: Mapped[str] = mapped_column(String(20), nullable=False, default="local", server_default="local")
    storage_object_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    indexing_state: Mapped[str] = mapped_column(String(20), nullable=False, default="queued", server_default="queued")
    indexing_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    indexed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class InviteToken(Base):
    """Single-use invite tokens for staff/board_member registration."""
    __tablename__ = "invite_tokens"
    __table_args__ = (
        CheckConstraint("role IN ('staff', 'board_member')", name="ck_invite_role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DocumentChunk(Base):
    """Embedded text chunks stored in Postgres via pgvector.

    Replaces the previous Chroma-on-disk vector store so vectors persist in
    Supabase alongside the rest of the application data.
    """
    __tablename__ = "document_chunks"

    # Deterministic per-chunk id: "{doc_id}__{chunk_index}" (same scheme the
    # Chroma version used) so deletes by doc_id and re-indexing stay simple.
    id: Mapped[str] = mapped_column(String(320), primary_key=True)
    doc_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    doc_name: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(settings.EMBEDDING_DIM), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    allowed_roles: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string, mirrors metadata
    document_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
