# Project Guide (Professional Modular Map)

This guide explains what each route, component, service, and utility does so you can follow the code quickly.

## Backend Route Map

- `GET /` in backend/app/main.py
  - Health-style root check.
- `POST /auth/register` in backend/app/api/auth.py
  - Registers normal users in Postgres users table.
- `POST /auth/login` in backend/app/api/auth.py
  - Sets HttpOnly auth cookie for admin UI session.
- `POST /auth/token` in backend/app/api/auth.py
  - OAuth2-compatible token route for Swagger/standard clients.
- `POST /auth/logout` in backend/app/api/auth.py
  - Clears auth cookie and ends browser session.
- `POST /documents/upload` in backend/app/api/documents.py
  - Admin upload route. Saves file (local or Supabase), then background-indexes to Chroma.
- `GET /documents/` in backend/app/api/documents.py
  - Lists manifest entries used by admin page.
- `POST /documents/{doc_id}/activate` in backend/app/api/documents.py
  - Toggles active/inactive retrieval state.
- `DELETE /documents/{doc_id}` in backend/app/api/documents.py
  - Removes vectors + manifest + local file + Supabase object (if present).
- `POST /rag/query` in backend/app/api/rag.py
  - Embeds question, retrieves top chunks, generates answer via provider fallback.
- `GET /students/` in backend/app/api/students.py
  - Admin-only list of students from Supabase table.
- `GET /students/{student_id}` in backend/app/api/students.py
  - Admin-only fetch one student.
- `POST /students/` in backend/app/api/students.py
  - Admin-only create student in Supabase.
- `PATCH /students/{student_id}` in backend/app/api/students.py
  - Admin-only partial update.
- `DELETE /students/{student_id}` in backend/app/api/students.py
  - Admin-only delete student.

## Backend Services and Utils

- backend/app/services/embeddings.py
  - Embedding fallback chain (Gemini -> Chroma default -> hash fallback).
- backend/app/services/llm.py
  - Answer synthesis fallback chain (Groq <-> Gemini -> extractive).
- backend/app/services/ingest.py
  - Text/PDF read, chunking, embedding, vector upsert, manifest registration.
- backend/app/services/storage.py
  - Storage abstraction (local + optional Supabase Storage).
- backend/app/services/students.py
  - Async SQLAlchemy operations for students (list/get/create/update/delete).
- backend/alembic/
  - Migration environment and versioned schema changes.
- backend/app/utils/fileio.py
  - Upload file writing and manifest management helpers.
- backend/app/utils/retry.py
  - Retry decorator used for external service resilience.

## Frontend Route Map (TypeScript)

- frontend/pages/index.tsx
  - Chat page calling `/rag/query`.
- frontend/pages/login.tsx
  - Admin login; server sets HttpOnly cookie (no localStorage token).
- frontend/pages/documents.tsx
  - Document upload and active/inactive management page.
- frontend/pages/students.tsx
  - Student CRUD dashboard page using `/students/*`.
- frontend/pages/_app.tsx
  - Global app entrypoint and Redux provider.

## Frontend Components and Helpers

- frontend/components/Layout.tsx
  - Shared page shell and nav links.
- frontend/lib/api.ts
  - Axios instance with credentialed cookie requests.
- frontend/lib/types.ts
  - Shared TypeScript models for API payloads.
- frontend/store/index.ts
  - Redux Toolkit store and auth slice.

## Supabase Setup You Must Do

1. Create Supabase project.
2. Set `DATABASE_URL` with Supabase Postgres connection string.
3. Run Alembic migration from backend folder:
  `SUPABASE_URL`: accepted as a fallback database URL if `DATABASE_URL` is empty
4. Create storage bucket matching `SUPABASE_BUCKET`.
5. Set backend env vars:
   - `SUPABASE_URL`
   - `SUPABASE_KEY` (service role key on backend)
  - `DATABASE_URL`
   - `SUPABASE_BUCKET`
   - `SUPABASE_STUDENTS_TABLE=students`
   - `STORAGE_BACKEND=supabase`
6. Keep keys out of git; put them in deployment environment variables.

## Current Professional Level

- Good: modular FastAPI services, retries/fallbacks, TypeScript frontend, DB-backed auth, HttpOnly session cookies, storage abstraction.
- Still needed for full enterprise grade: managed auth provider, role model in DB, API rate limiting, structured logging, metrics, integration tests, CI/CD checks, and background worker queue for heavy indexing.
