"""Async database engine/session setup.

Uses singleton engine/sessionmaker instances for efficient connection pooling.
"""

from collections.abc import AsyncGenerator
import ssl
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import log_db_target, settings

_engine = None
_sessionmaker = None


def _normalize_database_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    # Supabase often provides `postgresql://`; SQLAlchemy async uses asyncpg prefix.
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    # asyncpg does not support `sslmode` kwarg; SQLAlchemy will forward query params
    # as connect kwargs for asyncpg. Strip it from the URL query to avoid:
    # TypeError: connect() got an unexpected keyword argument 'sslmode'
    parts = urlsplit(url)
    if parts.query:
        query_items = [(k, v) for (k, v) in parse_qsl(parts.query, keep_blank_values=True) if k.lower() != "sslmode"]
        new_query = urlencode(query_items)
        url = urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))

    return url


def get_engine():
    global _engine
    if _engine is None:
        raw_url = settings.DATABASE_URL
        db_url = _normalize_database_url(raw_url)
        if not db_url:
            raise RuntimeError("DATABASE_URL is required for DB-backed auth and students.")

        connect_args = {}
        lowered_raw = (raw_url or "").lower()
        lowered = db_url.lower()
        if "sslmode=require" in lowered_raw or "supabase" in lowered_raw or "supabase" in lowered:
            if settings.DB_SSL_INSECURE:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            else:
                try:
                    ca_file = (settings.DB_SSL_CA_FILE or "").strip()
                    if ca_file:
                        ssl_context = ssl.create_default_context(cafile=ca_file)
                    else:
                        import certifi

                        ssl_context = ssl.create_default_context(cafile=certifi.where())
                except Exception:
                    ssl_context = ssl.create_default_context()
            connect_args = {"ssl": ssl_context}

        log_db_target()
        _engine = create_async_engine(db_url, pool_pre_ping=True, connect_args=connect_args)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    return _sessionmaker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async DB session per request."""

    session_factory = get_sessionmaker()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            try:
                await session.rollback()
            except Exception:
                pass
            raise
