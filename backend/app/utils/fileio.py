"""File I/O helpers plus the document manifest, now backed by Postgres.

The manifest used to be a JSON file inside the Chroma persist directory. It is
now stored in the ``document_metadata`` table so document state survives
ephemeral filesystems (e.g. Render). Function names/signatures are unchanged
so callers keep working; they just read/write rows via a sync session.
"""
import os
import json
import datetime
import uuid

try:
    import aiofiles
except Exception:  # pragma: no cover
    aiofiles = None

from sqlalchemy import select

from app.core.config import settings
from app.db.models import DocumentMetadata
from app.db.sync_session import get_sync_session

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Roles a document gets when registered outside the upload endpoint
# (e.g. scripts/index_existing.py) — effectively "everyone".
_DEFAULT_ROLES = '["student", "staff", "board_member", "admin"]'


def _entry_from_row(row: DocumentMetadata) -> dict:
    def _iso(value):
        if value is None:
            return None
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    return {
        "id": row.doc_id,
        "name": row.doc_name,
        "file_path": row.file_path,
        "uploaded_at": _iso(row.created_at),
        "indexing_state": row.indexing_state,
        "indexing_message": row.indexing_message,
        "indexed_at": _iso(row.indexed_at),
        "active": row.status == "active",
        "storage_backend": row.storage_backend,
        "storage_object_name": row.storage_object_name,
    }


def manifest_add(
    doc_id: str,
    name: str,
    file_path: str,
    active: bool = True,
    storage_backend: str = "local",
    storage_object_name: str = None,
):
    """Upsert a document-metadata row (upload endpoint pre-creates the row;
    script indexing creates it here)."""
    with get_sync_session() as session:
        row = session.scalar(select(DocumentMetadata).where(DocumentMetadata.doc_id == doc_id))
        if row is None:
            row = DocumentMetadata(
                doc_id=doc_id,
                doc_name=name,
                document_type="policy",
                allowed_roles=_DEFAULT_ROLES,
                status="active" if active else "inactive",
                uploaded_by=None,
                indexing_state="queued",
                indexing_message="Upload received. Indexing is queued.",
            )
            session.add(row)
        else:
            row.doc_name = name
            row.status = "active" if active else "inactive"
        row.file_path = file_path
        row.storage_backend = storage_backend
        row.storage_object_name = storage_object_name
        session.commit()


def manifest_list():
    with get_sync_session() as session:
        rows = session.scalars(select(DocumentMetadata).order_by(DocumentMetadata.created_at)).all()
        return [_entry_from_row(r) for r in rows]


def manifest_active_ids():
    """Return the list of active doc ids."""
    with get_sync_session() as session:
        return session.scalars(
            select(DocumentMetadata.doc_id).where(DocumentMetadata.status == "active")
        ).all()


def manifest_get(doc_id: str):
    with get_sync_session() as session:
        row = session.scalar(select(DocumentMetadata).where(DocumentMetadata.doc_id == doc_id))
        return _entry_from_row(row) if row is not None else None


def manifest_set_active(doc_id: str, active: bool):
    with get_sync_session() as session:
        row = session.scalar(select(DocumentMetadata).where(DocumentMetadata.doc_id == doc_id))
        if row is None:
            return False
        row.status = "active" if active else "inactive"
        session.commit()
        return True


def manifest_remove(doc_id: str):
    with get_sync_session() as session:
        row = session.scalar(select(DocumentMetadata).where(DocumentMetadata.doc_id == doc_id))
        if row is not None:
            session.delete(row)
            session.commit()


def manifest_update_indexing(
    doc_id: str,
    state: str,
    message: str | None = None,
    indexed_at: str | None = None,
):
    with get_sync_session() as session:
        row = session.scalar(select(DocumentMetadata).where(DocumentMetadata.doc_id == doc_id))
        if row is None:
            return False
        row.indexing_state = state
        if message is not None:
            row.indexing_message = message
        if indexed_at is not None:
            try:
                row.indexed_at = datetime.datetime.fromisoformat(indexed_at)
            except (TypeError, ValueError):
                row.indexed_at = datetime.datetime.utcnow()
        elif state == "indexed":
            row.indexed_at = datetime.datetime.utcnow()
        session.commit()
        return True


async def save_upload(upload_file) -> str:
    """Save a Starlette `UploadFile` object to disk and return path.

    This uses async file I/O to avoid blocking the event loop for large files.
    """
    filename = upload_file.filename
    safe_name = f"{uuid.uuid4().hex}_{filename}"
    dest = os.path.join(settings.UPLOAD_DIR, safe_name)
    chunk_size = 1024 * 1024
    if aiofiles is not None:
        async with aiofiles.open(dest, "wb") as fh:
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break
                await fh.write(chunk)
    else:
        # Fallback when aiofiles is unavailable in the runtime environment.
        with open(dest, "wb") as fh:
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break
                fh.write(chunk)
    return dest
