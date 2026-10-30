"""Application configuration using pydantic BaseSettings.

Place runtime overrides in a `.env` file at the backend root or set env vars.
"""
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "backend"


class Settings(BaseSettings):
    APP_NAME: str = "Kepler RAG Assistant"
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "please-change-this-secret")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    COOKIE_NAME: str = os.environ.get("COOKIE_NAME", "kc_access_token")
    COOKIE_SECURE: bool = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
    COOKIE_SAMESITE: str = os.environ.get("COOKIE_SAMESITE", "lax")
    STAFF_REGISTRATION_CODE: str = os.environ.get("STAFF_REGISTRATION_CODE", "")
    EMBEDDING_MODEL: str = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    # "local" = in-process MiniLM (needs ~300MB RAM); "gemini" = Gemini API, no local model.
    # Every vector in one database must come from the same provider.
    EMBEDDING_PROVIDER: str = os.environ.get("EMBEDDING_PROVIDER", "local")
    # Dimension of the pgvector column. If unset, resolved in the validator:
    # 768 for Gemini embeddings, 384 for the local MiniLM / hash fallback.
    EMBEDDING_DIM: int | None = None
    UPLOAD_DIR: str = os.environ.get("UPLOAD_DIR", "../data/uploads")
    # Production database. This is what the app uses unless USE_CLONE_DB is set.
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
    # Clone database for safe testing. Only used when USE_CLONE_DB=1 is set in the
    # terminal (process environment); a USE_CLONE_DB line in .env is ignored on purpose.
    DATABASE_URL_CLONE: str = os.environ.get("DATABASE_URL_CLONE", "")
    USE_CLONE_DB: bool = False

    # LLM / answer synthesis
    LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "extractive")
    # Accept common aliases so your existing root `.env` works without changes.
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", os.environ.get("MODEL_NAME", "gemini-3.8-flash"))
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.environ.get("GROQ_MODEL", os.environ.get("MODEL_NAME", "qwen/qwen3.8-27b"))
    LLM_TIMEOUT_S: int = int(os.environ.get("LLM_TIMEOUT_S", "30"))

    # Reserved for future production-grade persistence (not wired yet)
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")

    # DB TLS verification
    DB_SSL_CA_FILE: str = os.environ.get("DB_SSL_CA_FILE", "")
    DB_SSL_INSECURE: bool = os.environ.get("DB_SSL_INSECURE", "false").lower() == "true"

    # Supabase Storage (for uploaded documents)
    SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_SERVICE_ROLE_KEY", os.environ.get("SUPABASE_ANON_KEY", "")))
    SUPABASE_BUCKET: str = os.environ.get("SUPABASE_BUCKET", "kepler-documents")
    SUPABASE_STUDENTS_TABLE: str = os.environ.get("SUPABASE_STUDENTS_TABLE", "students")
    STORAGE_BACKEND: str = os.environ.get("STORAGE_BACKEND", "local")  # local | supabase

    # Professional RAG settings
    RAG_DISTANCE_THRESHOLD: float = float(os.environ.get("RAG_DISTANCE_THRESHOLD", "0.5"))
    RAG_MAX_CONTEXT_CHARS: int = int(os.environ.get("RAG_MAX_CONTEXT_CHARS", "3000"))
    RAG_RATE_LIMIT: str = os.environ.get("RAG_RATE_LIMIT", "10/minute")
    # Enable verbose RAG debug output (set RAG_DEBUG=true in your .env to enable)
    RAG_DEBUG: bool = False

    # Redis configuration for role-based rate limiting (local Redis for phase 1)
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    REDIS_PASSWORD: str = os.environ.get("REDIS_PASSWORD", "")
    
    # Role-based rate limits (requests per minute)
    RATE_LIMIT_STUDENT: int = int(os.environ.get("RATE_LIMIT_STUDENT", "10"))
    RATE_LIMIT_STAFF: int = int(os.environ.get("RATE_LIMIT_STAFF", "20"))
    RATE_LIMIT_ADMIN: int = int(os.environ.get("RATE_LIMIT_ADMIN", "50"))

    # Institutional email validation
    INSTITUTIONAL_DOMAIN: str = os.environ.get("INSTITUTIONAL_DOMAIN", "keplercollege.ac.rw")
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    # Extra allowed browser origins, comma-separated (FRONTEND_URL is always allowed).
    CORS_ORIGINS: str = os.environ.get("CORS_ORIGINS", "")

    model_config = SettingsConfigDict(
        env_file=(str(REPO_ROOT / ".env"), str(BACKEND_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="allow",
    )

    @model_validator(mode="after")
    def _select_database(self):
        # Terminal-only switch: read the real process environment, never .env.
        self.USE_CLONE_DB = os.environ.get("USE_CLONE_DB", "").strip().lower() in ("1", "true", "yes", "on")

        if self.USE_CLONE_DB:
            if not self.DATABASE_URL_CLONE:
                raise ValueError(
                    "USE_CLONE_DB is set but DATABASE_URL_CLONE is empty. "
                    "Add DATABASE_URL_CLONE to .env (and save it), or unset USE_CLONE_DB to use production."
                )
            self.DATABASE_URL = self.DATABASE_URL_CLONE
        elif not self.DATABASE_URL:
            # Legacy setups kept the production connection string in SUPABASE_URL.
            self.DATABASE_URL = self.SUPABASE_URL

        # The pgvector column is created with this size, so it is fixed at 384
        # (all-MiniLM-L6-v2) unless you deliberately migrate to another size.
        if self.EMBEDDING_DIM is None:
            self.EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", "384") or 384)
        return self


settings = Settings()


_db_target_logged = False


def db_target_label() -> str:
    """Human-readable database target (mode + host/db only; never credentials)."""
    parts = urlsplit(settings.DATABASE_URL or "")
    where = f"{parts.hostname or 'unknown-host'}:{parts.port or 5432}{parts.path or ''}"
    return f"{'CLONE' if settings.USE_CLONE_DB else 'PRODUCTION'} database -> {where}"


def log_db_target() -> None:
    """Print which database this process is connected to, once, on stderr."""
    global _db_target_logged
    if _db_target_logged or not settings.DATABASE_URL:
        return
    _db_target_logged = True
    print(f"[db] Using {db_target_label()}", file=sys.stderr, flush=True)

