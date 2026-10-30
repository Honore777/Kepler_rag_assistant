"""Synchronous database engine/session for non-request code paths.

The request path uses the async engine in ``app.db.session``. Background
indexing (``services.ingest``) and standalone scripts are synchronous, so they
get a dedicated psycopg2 engine here. Both point at the same ``DATABASE_URL``.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import log_db_target, settings
from app.db.session import _normalize_database_url

_engine = None
_sessionmaker = None


def _sync_database_url(url: str) -> str:
    """Convert the (already normalized) async URL to a psycopg2 one."""
    url = _normalize_database_url(url)
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "+psycopg2", 1)
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def get_sync_engine():
    global _engine
    if _engine is None:
        raw_url = settings.DATABASE_URL
        db_url = _sync_database_url(raw_url)
        if not db_url:
            raise RuntimeError("DATABASE_URL is required for DB-backed indexing.")

        connect_args = {}
        if "supabase" in (raw_url or "").lower() or "sslmode=require" in (raw_url or "").lower():
            if settings.DB_SSL_INSECURE:
                connect_args = {"sslmode": "require"}
            else:
                ca_file = (settings.DB_SSL_CA_FILE or "").strip()
                if ca_file:
                    connect_args = {"sslmode": "verify-full", "sslrootcert": ca_file}
                else:
                    connect_args = {"sslmode": "require"}

        log_db_target()
        _engine = create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)
    return _engine


def get_sync_session() -> Session:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = sessionmaker(get_sync_engine(), expire_on_commit=False, class_=Session)
    return _sessionmaker()
