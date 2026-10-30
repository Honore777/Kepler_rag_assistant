"""FastAPI app entry for Kepler RAG Assistant.

This file wires routers and middleware. Keep this file minimal — business logic
should live in `app.api`, `app.services`, and `app.db` modules.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from app.api import admin, auth, documents, rag, students, invites
from app.core.config import settings

app = FastAPI(title="Kepler RAG Assistant API", version="0.1.0")

# Allowed browser origins: local Next.js dev, the deployed frontend (FRONTEND_URL),
# and any extra comma-separated origins in CORS_ORIGINS.
origins = {"http://localhost:3000", "http://127.0.0.1:3000"}
if settings.FRONTEND_URL:
    origins.add(settings.FRONTEND_URL.strip().rstrip("/"))
origins.update(o.strip().rstrip("/") for o in settings.CORS_ORIGINS.split(",") if o.strip())
origins = sorted(origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."}
    )

app.include_router(auth.router, prefix="/auth", tags=["auth"])  # auth endpoints
app.include_router(documents.router, prefix="/documents", tags=["documents"])  # document mgmt
app.include_router(rag.router, prefix="/rag", tags=["rag"])  # RAG query endpoints
app.include_router(students.router, prefix="/students", tags=["students"])  # student records
app.include_router(invites.router, prefix="/invites", tags=["invites"])  # invite system
app.include_router(admin.router, prefix="/admin", tags=["admin"])  # admin dashboard data


@app.get("/")
def root():
    return {"status": "ok", "service": "kepler-rag"}
