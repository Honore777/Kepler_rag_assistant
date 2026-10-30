# Kepler RAG Assistant — Backend (FastAPI)

This folder contains a FastAPI backend scaffold for the Kepler RAG assistant.

Quick start (development):

1. Create a virtual environment and install dependencies from `requirements.txt`.

```bash
python -m venv .venv
source .venv/bin/activate     # or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. Run the app:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Notes:
- This scaffold provides document upload/indexing endpoints, DB-backed JWT auth with HttpOnly cookies, and a RAG query endpoint. It uses a Chroma vector store with layered embedding fallbacks.
- It also includes admin student CRUD endpoints backed by Supabase Postgres (`/students/*`).
- Some chromadb APIs vary by version — if you see runtime errors related to `chromadb.Client(...)` see `app/db/chroma_client.py` where fallbacks are implemented.
- For production: add HTTPS, rotate `SECRET_KEY`, use a real database for users and metadata, set strict CORS, and run behind a process manager.

Admin bootstrap (DB-backed):

```bash
python scripts/create_admin.py admin@example.com "your-password"
```

Migrations (Alembic):

```bash
alembic upgrade head
```

LLM answer synthesis:

- Default `LLM_PROVIDER=extractive` returns top retrieved passages.
- Set `LLM_PROVIDER=groq` (with `GROQ_API_KEY`) or `LLM_PROVIDER=gemini` (with `GEMINI_API_KEY`) for synthesized answers, with fallback handling.

Storage backends:

- Default `STORAGE_BACKEND=local` keeps uploaded files on local disk.
- Set `STORAGE_BACKEND=supabase` plus `SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_BUCKET` to also store uploads in Supabase Storage.

Supabase students table:

- Managed by SQLAlchemy models and Alembic migrations.
- Set `DATABASE_URL` and run `alembic upgrade head`.
- If you already keep the Supabase pooler URL in `SUPABASE_URL`, the app will use it as the database URL fallback.
