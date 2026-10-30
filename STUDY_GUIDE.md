# Study Guide — Kepler RAG Assistant

From-scratch walkthrough of the full RAG workflow: the tables, the upload
pipeline, the query pipeline, and how role-based access lets an admin publish
different documents to different audiences (students, teachers/staff, board).

---

## 1. The mental model

RAG = Retrieval-Augmented Generation. The LLM doesn't "know" your documents —
you retrieve the most relevant pieces and paste them into its prompt.

```
INGEST (once per document):
  file → extract text → split into chunks → embed each chunk → store in DB

QUERY (every question):
  question → embed → find nearest chunks in DB → permission check →
  stuff chunks into LLM prompt → answer + sources
```

Everything lives in **Supabase Postgres** now. There is no separate vector
database and no state on disk that matters (uploaded files are cached locally
but the source of truth can be Supabase Storage).

---

## 2. The tables — know these four

```
┌─────────────────────┐         ┌──────────────────────────┐
│ "user"              │         │ document_metadata        │
│  id (uuid)          │         │  id (uuid)               │
│  username (email)   │         │  doc_id ─────┐           │
│  role             │◄─────┐    │  doc_name    │           │
│  password_hash    │      │    │  allowed_roles (JSON)    │
└─────────────────────┘      │    │  status (active/...)   │
                             │    │  document_type         │
┌─────────────────────┐      │    │  indexing_state        │
│ students            │      │    │  file_path / storage_* │
│  student_code       │      │    │  file_size / file_type │
│  full_name, email   │      │    │  uploaded_by ─► "user" │
│  program, status    │      │    │  indexed_at            │
└─────────────────────┘      │    └──────────────────────┘
                             │              │
                             │              │ 1 doc : N chunks
                             │              ▼
                             │    ┌──────────────────────────┐
                             │    │ document_chunks          │
                             │    │  id = "{doc_id}__{i}"    │
                             │    │  doc_id ◄────────────────┘
                             │    │  chunk_index             │
                             │    │  content (the text)      │
                             │    │  embedding vector(384)   │
                             │    │  active, allowed_roles,  │
                             │    │  document_type           │
                             │    └──────────────────────────┘
                             │
  role (student/staff/board_member/admin) decides which doc_ids
  the user may retrieve from document_chunks.
```

| Table | Role in the system |
|---|---|
| `user` | Login accounts. `role` drives every access decision. Admin created only via `scripts/create_admin.py`. |
| `students` | Student *records* managed by admin (separate from login accounts). |
| `document_metadata` | One row per uploaded document: permissions, lifecycle status, indexing state, storage info. **Also serves as the manifest** (replaced the old JSON file). |
| `document_chunks` | Many rows per document: the actual searchable text + its embedding vector. This is what used to be Chroma. |

---

## 3. Admin upload flow — step by step

Admin uploads `staff-handbook.pdf` with `allowed_roles=["staff"]`,
`document_type="handbook"`, `active=true`.

**Step 1 — `POST /documents/upload`** (`app/api/documents.py:61`)

- `require_admin` checks the JWT cookie's role is `admin`.
- `allowed_roles` is validated: must be a JSON list ⊆ `{student, staff, board_member, admin}` — this is the **entire access-control contract** for the document.
- A `document_metadata` row is inserted immediately with `status="active"`, `indexing_state="queued"`. The UI can show "indexing queued" right away.
- The file is saved (`services/storage.py` → local `UPLOAD_DIR`, or Supabase Storage when `STORAGE_BACKEND=supabase`).
- A **background task** is queued for indexing; the HTTP response returns instantly.

**Step 2 — `_index_background` → `index_document`** (`app/services/ingest.py:55`)

a. `load_document()` — LangChain loaders extract text (PDF, txt, etc.).

b. `split_text()` — `RecursiveCharacterTextSplitter`, `chunk_size=800`,
   `overlap=100` (`ingest.py:30`). Tries `\n\n`, then `\n`, then space — so it
   cuts at paragraph/sentence boundaries. The 100-char overlap means a rule
   straddling a boundary appears in *both* chunks → retrieval never loses it.

c. `embed_texts(chunks)` — each chunk → a vector: 384 floats via local
   `all-MiniLM-L6-v2` (sentence-transformers), or 768 floats if
   `GEMINI_API_KEY` is set (`task_type="retrieval_document"`). An embedding is
   just "meaning as coordinates": texts about similar topics land near each
   other in 384-D space.

d. **Dimension guard** (`ingest.py:112`) — if the embedder's output doesn't
   match `EMBEDDING_DIM`, it fails loudly. (The old Chroma code silently
   spawned parallel collections per dimension — a debugging nightmare.)

e. **Write to `document_chunks`** (`ingest.py:136`) — delete any old chunks for
   this `doc_id`, then insert one row per chunk:
   `id="{doc_id}__{i}"`, `content=chunk text`, `embedding=vector`,
   plus copies of `doc_name`, `allowed_roles`, `document_type` for convenience.

f. `manifest_add()` upserts the `document_metadata` row with `file_path`,
   `storage_backend`, `storage_object_name` (`app/utils/fileio.py:60`).

g. Status updates land in `indexing_state` / `indexing_message` /
   `indexed_at` on the same row: `queued → processing → indexed | failed`.
   The admin dashboard reads this via `GET /documents`.

**Result:** the document is now *searchable*, but only by the roles listed in
`allowed_roles`. Upload with `["staff","board_member"]` → only teachers and
board members retrieve it; `["student","staff","board_member","admin"]` → everyone.

---

## 4. Teacher/student query flow — step by step

Teacher logs in, asks "What is the leave policy?" → `POST /rag/query`
(`app/api/rag.py:29`).

**Step 1 — identity.** `get_current_user` decodes the JWT from the HttpOnly
cookie → `{username, role}` (e.g. `role="staff"`). Rate limiter checks
per-role quota (student 10/min, staff 20/min, admin 50/min — Redis, fails open
if Redis is down).

**Step 2 — permission set.** `filter_documents_by_role(db, "staff", email, doc_ids)`
(`app/services/document_filter.py:179`) queries `document_metadata` and keeps
only rows where:
- `status == "active"` and not expired
- `"staff"` ∈ `allowed_roles` (JSON parsed per row)
- for students: email must end with `@keplercollege.ac.rw`

Output: `allowed_doc_ids = {"abc-...", "def-...", ...}` — the docs *this* user
may see.

**Step 3 — embed the question.** Same embedder, but
`task_type="retrieval_query"` — Gemini is trained to encode questions and
documents asymmetrically.

**Step 4 — vector search with permissions baked in** (`rag.py:76-91`):

```sql
SELECT *, embedding <=> :query_vec AS distance
FROM document_chunks
WHERE doc_id IN (allowed_doc_ids)   -- 🔐 enforced in SQL
  AND active = true
ORDER BY distance
LIMIT 30;
```

`embedding <=> vec` is pgvector's **cosine distance** = `1 − similarity`
(0 = identical meaning, 2 = opposite). The HNSW index on the column makes it
fast even with millions of chunks. Key point: permission filtering happens
*inside the query* — the DB never even considers chunks from documents the
user can't see. (The old Chroma version retrieved the global top-K first and
filtered in Python — a staff-only corpus could starve a student's results.)

**Step 5 — threshold filter** (`rag.py:111`): chunks with
`distance > RAG_DISTANCE_THRESHOLD` (0.5 ⇒ cosine similarity < 0.5) are
dropped as weak matches. Tune this: too many "no relevant info" → raise it;
too many wrong answers → lower it. Note it's now a true cosine distance —
Chroma's old scale was ~2× different.

**Step 6 — context budget** (`rag.py:137`): surviving chunks are packed into
the prompt until `RAG_MAX_CONTEXT_CHARS` (3000) or `top_k` is hit — caps LLM
cost and prompt size.

**Step 7 — generate.** `generate_answer()` sends question + chunks to Groq,
Gemini, or the extractive fallback (`LLM_PROVIDER`). The response includes
`answer` + `sources` (each with `doc_name`, `chunk_index`, similarity score)
→ the UI can show "from: Staff Handbook, chunk 12".

---

## 5. How "different documents for different teachers" works

The unit of access control is the **role**, not the individual teacher.

```
Admin uploads:
  "All-Staff Memo"       allowed_roles = [staff, board_member, admin]
  "Math Dept Research"   allowed_roles = [staff]                  → all staff
  "Board Finances"       allowed_roles = [board_member, admin]    → hidden from staff
  "Student Handbook"     allowed_roles = [student, staff, ...]    → everyone
```

At query time, `document_metadata.allowed_roles` ∩ `user.role` decides which
`doc_id`s enter the vector search. A teacher asking a question physically
cannot retrieve chunks from "Board Finances" — the SQL `WHERE doc_id IN (...)`
excludes them before similarity is even computed.

**Teacher accounts are created two ways** (`app/api/auth.py:88`,
`app/api/invites.py`):
- Self-register with `role=staff`/`board` + the shared
  `STAFF_REGISTRATION_CODE` env var.
- `/invites/generate` → `/invites/register-with-invite`: the admin generates a
  single-use, expiring `invite_tokens` row bound to an email + role;
  `register-with-invite` validates it (exists, unused, unexpired, email match)
  and assigns the role **from the token** — clients can't pick their own role.
- Password change: `POST /auth/change-password` (authenticated, verifies the
  current password, IP rate-limited).

**Honest limitations:**
- All staff see all staff docs — no per-teacher or per-department
  granularity yet. (Schema supports `department` on `document_metadata`; the
  filter has a placeholder for it. Per-teacher access would need a
  `document_access(document_id, user_id)` junction table.)
- `allowed_roles` is copied onto chunks but the *metadata row* is authoritative
  — the copy exists for debugging/display.

---

## 6. Chroma → pgvector: what the migration changed

| Concern | Before (Chroma) | After (pgvector) |
|---|---|---|
| Vector storage | `chroma_db/` files on container disk | `document_chunks` table, Supabase |
| Manifest | `documents_manifest.json` on disk | columns on `document_metadata` |
| Retrieval | `collection.query(...)` → dict of lists | SQL `ORDER BY embedding <=> :vec` |
| Permission filter | in Python, after retrieval | in SQL `WHERE` clause |
| Distance metric | squared L2 (~2× cosine dist) | cosine distance `<=>` |
| Dim mismatch | silent parallel collections `name_{dim}d` | loud error vs `EMBEDDING_DIM` |
| Delete doc | `collection.delete(where=...)` best-effort | `DELETE WHERE doc_id = ?` |
| Persistence on Render | wiped every deploy | survives — it's Postgres |

Files that changed: `models.py` (+`DocumentChunk`, +manifest columns),
`ingest.py` (insert rows), `rag.py` (SQL retrieval), `fileio.py` (manifest →
DB-backed sync functions), `documents.py` (delete path), `embeddings.py`
(query/document task types, no Chroma fallback), new `sync_session.py`
(psycopg2 engine for the sync indexing path — async engine stays for requests),
new migration `20261030_0003`, `config.py` (`DATABASE_URL_CLONE`,
`EMBEDDING_DIM`). `chroma_client.py` deleted.

`DATABASE_URL` empty → everything (app + alembic) uses `DATABASE_URL_CLONE`.
Set the real `DATABASE_URL` on Render to go live.

---

## 7. Improvement roadmap (ordered by value)

1. **Per-teacher / per-department access** — `document_access` junction table
   or use the existing `department` column; today access is per-role only.
2. **Hybrid search** — add Postgres `tsvector` full-text and fuse scores;
   vectors alone miss exact names/codes/dates.
3. **Better chunking** — split on document structure (headings); embed
   `doc_name + chunk` so chunks carry context.
4. **Batch embeddings** — Gemini's `embed_content` accepts batches; ingestion
   currently loops one call per chunk.
5. **Re-ranking** — retrieve 20, cross-encode, keep 5.
6. **Supabase RLS** on `document_chunks` — defense-in-depth below the app.
7. **Token revocation** — JWTs are stateless; a password change doesn't
   invalidate already-issued tokens (they live up to
   `ACCESS_TOKEN_EXPIRE_MINUTES` = 24h). Add a `password_changed_at` check if
   that matters.

## 8. Verify on the clone DB

```bash
cd backend
alembic upgrade head                      # applies 20261030_0003 to the clone
python scripts/index_existing.py          # index the handbook → document_chunks
uvicorn app.main:app --reload --port 8000
```

In Supabase dashboard: Database → Extensions → `vector`; Table Editor →
`document_chunks` (`select doc_id, count(*) from document_chunks group by 1`).
Set `RAG_DEBUG=true` to get retrieved/filtered counts in every `/rag/query`
response.
