"""Professional document ingestion using LangChain and pgvector.

This module provides production-grade document processing with:
- LangChain-based document loading for multiple formats
- Intelligent text splitting with overlap
- Embedding and indexing into Postgres (pgvector)
- Manifest tracking for admin management
"""
import json
import uuid
from typing import List

from sqlalchemy import delete

from app.core.config import settings
from app.services.embeddings import embed_texts
from app.db.models import DocumentChunk
from app.db.sync_session import get_sync_session
from app.utils.fileio import manifest_add
from app.services.document_loader import load_document, DocumentLoadError

# LangChain for professional text splitting
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


def split_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """Professional text splitting using LangChain or fallback."""
    if LANGCHAIN_AVAILABLE:
        # Use LangChain's recursive character text splitter for better results
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", " ", ""],  # Hierarchical separators
            length_function=len,
        )
        return splitter.split_text(text)
    else:
        # Fallback to naive splitter if LangChain not available
        chunks = []
        start = 0
        length = len(text)
        while start < length:
            end = min(start + chunk_size, length)
            chunks.append(text[start:end])
            if end >= length:
                break
            start = max(0, end - overlap)
        return chunks


def index_document(
    file_path: str,
    doc_name: str,
    doc_id: str = None,
    active: bool = True,
    allowed_roles: list[str] | None = None,
    document_type: str = "policy",
    storage_backend: str = "local",
    storage_object_name: str = None,
) -> str:
    """Professional document indexing using LangChain and Chroma.

    Loads documents with LangChain, splits intelligently, embeds and stores in Chroma.
    Returns the `doc_id` assigned to this document. A manifest entry is also
    written so the admin UI can list and toggle this document.
    """
    if doc_id is None:
        doc_id = str(uuid.uuid4())

    try:
        # Use professional LangChain document loading
        documents = load_document(file_path)
        
        if not documents:
            raise DocumentLoadError(f"No content loaded from {file_path}")
        
        # Extract text from LangChain documents
        all_text = ""
        for doc in documents:
            if hasattr(doc, 'page_content'):
                all_text += doc.page_content + "\n"
            else:
                all_text += str(doc) + "\n"
        
        # Clean up text
        all_text = all_text.strip()
        if not all_text:
            raise DocumentLoadError(f"No extractable text content in {file_path}")
        
        # Split text using professional splitter
        chunks = split_text(all_text)
        
        if not chunks:
            raise DocumentLoadError(f"No text chunks created from {file_path}")
        
        # Generate embeddings
        embeddings = embed_texts(chunks)
        
        if len(embeddings) != len(chunks):
            raise DocumentLoadError(f"Embedding mismatch: {len(embeddings)} vs {len(chunks)} chunks")
        
    except DocumentLoadError as e:
        raise RuntimeError(f"Document processing failed: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error processing {file_path}: {str(e)}")

    embedding_dim = len(embeddings[0]) if embeddings else 0
    if embedding_dim != settings.EMBEDDING_DIM:
        raise RuntimeError(
            f"Embedding dimension {embedding_dim} does not match EMBEDDING_DIM "
            f"{settings.EMBEDDING_DIM}. Update EMBEDDING_DIM or the embedding provider "
            "configuration, then re-run migrations."
        )

    roles_json = json.dumps(allowed_roles) if allowed_roles is not None else None

    rows = [
        DocumentChunk(
            id=f"{doc_id}__{i}",
            doc_id=doc_id,
            doc_name=doc_name,
            chunk_index=i,
            content=chunk,
            embedding=emb,
            active=bool(active),
            allowed_roles=roles_json,
            document_type=document_type or None,
        )
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
    ]

    with get_sync_session() as session:
        # Re-index safety: drop any previous chunks for this doc.
        session.execute(delete(DocumentChunk).where(DocumentChunk.doc_id == doc_id))
        session.add_all(rows)
        session.commit()

    # Register in the manifest (document_metadata) for the admin UI
    manifest_add(
        doc_id,
        doc_name,
        file_path,
        active,
        storage_backend=storage_backend,
        storage_object_name=storage_object_name,
    )
    return doc_id

