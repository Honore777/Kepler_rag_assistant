# Kepler RAG Assistant (Production-Oriented)

This repository is a **Retrieval-Augmented Generation (RAG)** assistant intended for an institutional setting (students + staff). The current direction is:

- **Frontend:** Next.js + Tailwind + TypeScript
- **Backend:** FastAPI
- **Vector store:** pgvector inside Postgres (Supabase) — no separate vector DB needed
- **Document management:** upload, delete, activate/deactivate documents used by retrieval
- **Student management:** Supabase-backed students CRUD for admin workflows
- **LLM fallback:** Groq/Gemini with extractive fallback (configurable via `.env`)
- **Storage options:** local disk (default) or Supabase Storage

## What’s Included

- RAG endpoint that retrieves from **active documents** by default
- Admin-only document endpoints (DB-backed JWT auth in HttpOnly cookies)
- Retries (exponential backoff) for external calls (Gemini)
- Singleton-style initialization for heavy clients (Chroma client; local embedding model if enabled)

## Local Development

### 1) Backend (FastAPI)

Install backend deps (recommended in a virtualenv/conda env):

```bash
python -m pip install -r backend/requirements.txt
```

Run DB migrations first:

```bash
cd backend
alembic upgrade head
cd ..
```

Create an admin user:

```bash
python backend/scripts/create_admin.py admin@example.com "your-password"
```

Run the API:

```bash
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

### 2) Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Open:
- Chat: `http://localhost:3000/`
- Document manager: `http://localhost:3000/documents`
- Students manager: `http://localhost:3000/students`
- Admin login: `http://localhost:3000/login`

## Environment Variables

Backend reads `.env` (and ignores unknown keys). Key settings:

- `SECRET_KEY`: JWT signing secret (must be changed in production)
- `DATABASE_URL`: Postgres async connection URL (Supabase). Required.
- `DATABASE_URL_CLONE`: optional clone DB used for testing when `DATABASE_URL` is empty
- `EMBEDDING_DIM`: pgvector column dimension (default: 768 with `GEMINI_API_KEY`, else 384)
- `UPLOAD_DIR`: where uploaded documents are stored locally (ephemeral on free hosts)
- `LLM_PROVIDER`: `extractive`, `groq`, or `gemini`
- `GROQ_API_KEY`: required if using Groq
- `GEMINI_API_KEY`: required if using Gemini
- `STORAGE_BACKEND`: `local` or `supabase`
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_BUCKET`: required when `STORAGE_BACKEND=supabase`
- `SUPABASE_STUDENTS_TABLE`: students table name (default: `students`)
- `COOKIE_NAME`, `COOKIE_SECURE`, `COOKIE_SAMESITE`: auth cookie controls

See [backend/.env.example](backend/.env.example) for a starter.
See [PROJECT_GUIDE.md](PROJECT_GUIDE.md) for route/component/utils explanations.

## Notes for Production

- Consider replacing local JWT login with external identity (SSO/OAuth2) if institution policy requires it
- Add rate limiting, audit logs, and monitoring
- Run behind HTTPS and a production ASGI server configuration
- For Supabase Storage, prefer `SUPABASE_SERVICE_ROLE_KEY` (or map it into `SUPABASE_KEY`) on the server side only