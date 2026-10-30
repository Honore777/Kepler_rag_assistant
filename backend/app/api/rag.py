"""RAG query endpoint with professional-grade retrieval and role-based rate limiting.

This endpoint performs controlled RAG with:
- Distance-based scoring and threshold filtering
- Context size limiting to prevent LLM overload
- Role-based rate limiting (student: 10/min, staff: 20/min, admin: 50/min)
- Safe generation with context validation
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import QueryRequest, QueryResponse, SourceItem
from app.services.embeddings import embed_texts
from app.services.llm import generate_answer
from app.db.models import DocumentChunk
from app.services.document_filter import filter_documents_by_role
from app.core.config import settings
from app.db.session import get_db

# Role-based rate limiting
from app.decorators.rate_limit import rate_limit_by_role, get_rate_limit_stats

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
@rate_limit_by_role()  # Role-based rate limiting (student: 10/min, staff: 20/min, admin: 50/min)
async def query_rag(request: Request, payload: QueryRequest, db: AsyncSession = Depends(get_db)):
    """Professional RAG query with role-based document filtering and rate limiting."""
    
    # Input validation
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if len(payload.question) > 1000:
        raise HTTPException(status_code=400, detail="Question too long (max 1000 chars)")

    # 🔥 Get user information for role-based filtering
    from app.core.auth_deps import get_current_user
    user = await get_current_user(request, db)
    user_role = user.get("role", "student")
    user_email = user.get("username")

    # Embed the user question
    q_emb = embed_texts([payload.question], for_query=True)[0]

    # 🔥 Role-based document filtering - only accessible documents
    if payload.doc_ids:
        # Filter specific documents by user role
        allowed_doc_ids = set(await filter_documents_by_role(db, user_role, user_email, payload.doc_ids))
    else:
        # Get all documents accessible to this user
        allowed_doc_ids = set(await filter_documents_by_role(db, user_role, user_email, []))

    # Use pydantic settings so `.env` values are loaded via Settings.env_file
    debug_enabled = getattr(settings, "RAG_DEBUG", False)
    debug_info = None
    if debug_enabled:
        debug_info = {
            "user_role": user_role,
            "allowed_doc_ids_count": len(allowed_doc_ids),
            "allowed_doc_ids_sample": list(sorted(allowed_doc_ids))[:5],
        }

    # Request more results for filtering - we'll filter by distance later
    requested = max(payload.top_k * 3, 10)

    # ✅ FIX 1: pgvector cosine-distance search, restricted to documents the
    # user is allowed to see.
    texts: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []
    distances: list[float] = []

    if allowed_doc_ids:
        distance = DocumentChunk.embedding.cosine_distance(q_emb).label("distance")
        stmt = (
            select(DocumentChunk, distance)
            .where(
                DocumentChunk.doc_id.in_(allowed_doc_ids),
                DocumentChunk.active.is_(True),
            )
            .order_by(distance)
            .limit(requested)
        )
        rows = (await db.execute(stmt)).all()
        for chunk, dist in rows:
            ids.append(chunk.id)
            texts.append(chunk.content)
            distances.append(float(dist))
            metadatas.append({
                "doc_id": chunk.doc_id,
                "doc_name": chunk.doc_name,
                "chunk_index": chunk.chunk_index,
                "document_type": chunk.document_type,
                "allowed_roles": chunk.allowed_roles,
            })

    collection_used = "document_chunks"

    # ✅ FIX 2: Filter weak chunks by distance threshold
    filtered_sources = []
    filtered_by_distance = 0
    filtered_by_role = 0
    for i, txt in enumerate(texts):
        if i >= len(distances):
            break
            
        # Skip if distance is too high (poor match)
        if distances[i] > settings.RAG_DISTANCE_THRESHOLD:
            filtered_by_distance += 1
            continue
            
        meta = metadatas[i] if i < len(metadatas) else {}
        doc_id = meta.get("doc_id")
        
        # Skip if document not in allowed list
        if allowed_doc_ids and doc_id not in allowed_doc_ids:
            filtered_by_role += 1
            continue
            
        sid = ids[i] if i < len(ids) else f"src_{i}"
        filtered_sources.append(SourceItem(id=sid, metadata=meta, text=txt, score=1.0 - distances[i]))

    if debug_enabled and debug_info is not None:
        debug_info.update({
            "retrieved_chunks": len(texts),
            "filtered_by_distance": filtered_by_distance,
            "filtered_by_role": filtered_by_role,
            "filtered_sources": len(filtered_sources),
            "distance_threshold": settings.RAG_DISTANCE_THRESHOLD,
            "collection_used": collection_used,
        })

    # ✅ FIX 3: Limit context size to prevent LLM overload
    context_texts = []
    total_chars = 0
    
    for source in filtered_sources:
        if total_chars + len(source.text) > settings.RAG_MAX_CONTEXT_CHARS:
            break
        context_texts.append(source.text)
        total_chars += len(source.text)
        
        if len(context_texts) >= payload.top_k:
            break

    # ✅ FIX 4: Safer generation with context validation
    if not context_texts:
        answer = "No relevant information found in the selected documents."
        sources_for_response = []
    else:
        answer = generate_answer(payload.question, context_texts, payload.history)
        # Return only the sources that were actually used
        sources_for_response = filtered_sources[:len(context_texts)]

    return QueryResponse(answer=answer, sources=sources_for_response, debug=debug_info)


@router.get("/rate-limit-stats")
@get_rate_limit_stats()
async def get_rate_limit_stats(request: Request):
    """Get current rate limit statistics for authenticated user."""
    if hasattr(request.state, 'rate_limit_stats'):
        return request.state.rate_limit_stats
    else:
        return {"error": "Rate limit stats not available"}
