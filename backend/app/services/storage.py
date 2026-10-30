"""Storage backend abstraction.

We support:
- local filesystem (default)
- Supabase Storage (recommended for production)

This keeps document storage decoupled from ingestion/indexing logic.
"""

import os
import uuid
from typing import Optional, Tuple

from app.core.config import settings


def _safe_object_name(filename: str) -> str:
    filename = filename or "upload.bin"
    return f"{uuid.uuid4().hex}_{filename}"


async def save_upload(upload_file) -> Tuple[str, Optional[str]]:
    """Save upload and return (local_path, storage_object_name_or_none).

    We always save locally first because ingestion reads from disk.
    If Supabase is enabled, we also upload the file to Supabase Storage.
    """

    from app.utils.fileio import save_upload as save_local

    local_path = await save_local(upload_file)
    backend = (settings.STORAGE_BACKEND or "local").lower().strip()
    if backend != "supabase":
        return local_path, None

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        # Misconfigured: keep local only.
        return local_path, None

    object_name = _safe_object_name(upload_file.filename)
    ok = await _supabase_upload(local_path, object_name)
    if not ok:
        return local_path, None
    return local_path, object_name


async def delete_object(object_name: Optional[str]) -> None:
    backend = (settings.STORAGE_BACKEND or "local").lower().strip()
    if backend != "supabase" or not object_name:
        return
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return
    await _supabase_delete(object_name)


async def _supabase_upload(local_path: str, object_name: str) -> bool:
    """Upload a file to Supabase Storage."""
    try:
        from supabase import create_client
    except Exception:
        return False

    try:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        bucket = client.storage.from_(settings.SUPABASE_BUCKET)

        with open(local_path, "rb") as fh:
            data = fh.read()

        # upsert=True lets admins replace documents with same name if you choose to.
        bucket.upload(object_name, data, {"upsert": True})
        return True
    except Exception:
        return False


async def _supabase_delete(object_name: str) -> None:
    try:
        from supabase import create_client
    except Exception:
        return

    try:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        bucket = client.storage.from_(settings.SUPABASE_BUCKET)
        bucket.remove([object_name])
    except Exception:
        return
