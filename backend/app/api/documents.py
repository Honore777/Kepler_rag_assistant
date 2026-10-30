"""Document management API: upload, list, activate, delete.

These endpoints are intentionally straightforward: admin clients can upload
files (text for now), which are indexed into pgvector in a background task.
"""
import uuid
import os
import json
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends, Form
from typing import List
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.fileio import manifest_list, manifest_set_active, manifest_remove, manifest_get
from app.services.ingest import index_document
from app.services.storage import save_upload, delete_object
from app.core.config import settings
from app.models.schemas import DocumentCreateResponse, DocumentItem
from app.core.auth_deps import require_admin
from app.db.models import DocumentChunk, DocumentMetadata
from app.db.session import get_db
from app.utils.fileio import manifest_update_indexing

router = APIRouter()


def _index_background(
    file_path: str,
    filename: str,
    doc_id: str = None,
    active: bool = True,
    allowed_roles: list[str] | None = None,
    document_type: str = "policy",
    storage_backend: str = "local",
    storage_object_name: str = None,
):
    # Synchronous call intentionally placed in a background thread by FastAPI
    if doc_id:
        manifest_update_indexing(doc_id, "processing", "Indexing is in progress...")

    try:
        index_document(
            file_path,
            doc_name=filename,
            doc_id=doc_id,
            active=active,
            allowed_roles=allowed_roles,
            document_type=document_type,
            storage_backend=storage_backend,
            storage_object_name=storage_object_name,
        )
        if doc_id:
            manifest_update_indexing(doc_id, "indexed", "Document indexed successfully.")
    except Exception as e:
        if doc_id:
            manifest_update_indexing(doc_id, "failed", f"Indexing failed: {str(e)}")


@router.post("/upload", response_model=DocumentCreateResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    active: bool = True,
    allowed_roles: str = Form(...),
    document_type: str = Form("policy"),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Upload a file and index it asynchronously.

    Returns a minimal document record immediately; indexing happens in the
    background so the API is responsive for large files.
    """
    doc_id = str(uuid.uuid4())

    try:
        roles_list = json.loads(allowed_roles) if allowed_roles else []
        if not isinstance(roles_list, list) or not all(isinstance(r, str) for r in roles_list):
            raise ValueError("allowed_roles must be a JSON list of strings")
    except Exception:
        raise HTTPException(status_code=400, detail="allowed_roles must be a JSON array (e.g. ['student','staff'])")

    roles_list = [r.strip() for r in roles_list if r and isinstance(r, str)]
    if not roles_list:
        raise HTTPException(status_code=400, detail="allowed_roles cannot be empty")

    valid_roles = {"student", "staff", "board_member", "admin"}
    if any(r not in valid_roles for r in roles_list):
        raise HTTPException(status_code=400, detail=f"allowed_roles must be subset of {sorted(valid_roles)}")

    valid_document_types = {"policy", "research", "handbook", "procedure", "other"}
    if document_type not in valid_document_types:
        raise HTTPException(status_code=400, detail=f"document_type must be one of {sorted(valid_document_types)}")

    try:
        admin_uuid = uuid.UUID(str(admin["id"]))
    except Exception:
        raise HTTPException(status_code=500, detail="Invalid admin id in auth context")

    # Upsert metadata row (authoritative for access control)
    existing = await db.execute(select(DocumentMetadata).where(DocumentMetadata.doc_id == doc_id))
    meta = existing.scalar_one_or_none()
    if meta is None:
        meta = DocumentMetadata(
            doc_id=doc_id,
            doc_name=file.filename,
            document_type=document_type,
            allowed_roles=json.dumps(roles_list),
            status="active" if active else "inactive",
            file_size=None,
            file_type=None,
            uploaded_by=admin_uuid,
        )
        db.add(meta)
    else:
        meta.doc_name = file.filename
        meta.document_type = document_type
        meta.allowed_roles = json.dumps(roles_list)
        meta.status = "active" if active else "inactive"
        meta.uploaded_by = admin_uuid
    await db.commit()

    path, storage_object_name = await save_upload(file)
    file_size = os.path.getsize(path) if os.path.exists(path) else None
    file_type = os.path.splitext(file.filename or "")[1].lstrip(".").lower() or None

    meta.file_size = file_size
    meta.file_type = file_type
    meta.description = meta.description or None
    await db.commit()

    backend_name = (settings.STORAGE_BACKEND or "local").lower().strip()
    background_tasks.add_task(
        _index_background,
        path,
        file.filename,
        doc_id,
        active,
        roles_list,
        document_type,
        backend_name,
        storage_object_name,
    )
    return DocumentCreateResponse(id=doc_id, name=file.filename, active=active, message="Upload received. Indexing is queued.")


@router.get("/", response_model=List[DocumentItem])
async def list_documents(db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    raw = manifest_list()

    result = await db.execute(select(DocumentMetadata))
    metadata_rows = {row.doc_id: row for row in result.scalars().all()}

    items: list[DocumentItem] = []
    for entry in raw:
        meta = metadata_rows.get(entry.get("id"))
        allowed_roles: list[str] | None = None
        if meta is not None and meta.allowed_roles:
            try:
                parsed_roles = json.loads(meta.allowed_roles)
                if isinstance(parsed_roles, list):
                    allowed_roles = [r for r in parsed_roles if isinstance(r, str)]
            except Exception:
                allowed_roles = None

        created_at = None
        if meta is not None and meta.created_at is not None:
            created_at = meta.created_at.isoformat() if hasattr(meta.created_at, "isoformat") else str(meta.created_at)

        items.append(
            DocumentItem(
                id=entry.get("id"),
                name=entry.get("name") or (meta.doc_name if meta is not None else "Untitled"),
                type=meta.document_type if meta is not None else entry.get("type"),
                allowed_roles=allowed_roles,
                active=entry.get("active", True) if meta is None else meta.status == "active",
                status=meta.status if meta is not None else ("active" if entry.get("active", True) else "inactive"),
                file_size=meta.file_size if meta is not None else None,
                created_at=created_at,
                uploaded_at=entry.get("uploaded_at"),
                indexing_state=entry.get("indexing_state"),
                indexing_message=entry.get("indexing_message"),
                indexed_at=entry.get("indexed_at"),
            )
        )

    return items


@router.post("/{doc_id}/activate")
async def set_active(doc_id: str, active: bool, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    ok = manifest_set_active(doc_id, active)
    if not ok:
        raise HTTPException(status_code=404, detail="document not found")

    result = await db.execute(select(DocumentMetadata).where(DocumentMetadata.doc_id == doc_id))
    meta = result.scalar_one_or_none()
    if meta is not None:
        meta.status = "active" if active else "inactive"
        await db.commit()
    return {"status": "ok", "id": doc_id, "active": active}


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    # Remove vectors for this document from pgvector.
    await db.execute(delete(DocumentChunk).where(DocumentChunk.doc_id == doc_id))
    await db.commit()

    entry = manifest_get(doc_id)
    if entry:
        await delete_object(entry.get("storage_object_name"))
        local_path = entry.get("file_path")
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass

    # Removes the document_metadata row (the manifest).
    manifest_remove(doc_id)
    return {"status": "ok", "id": doc_id}
