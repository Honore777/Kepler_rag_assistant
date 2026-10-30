"""Embedding service.

Priority order:
1) Gemini embeddings (if `GEMINI_API_KEY` is set)
2) Sentence-transformers when `EMBEDDING_MODEL` is configured
3) Deterministic hash fallback (emergency only, low quality)

All paths must return vectors of dimension ``settings.EMBEDDING_DIM`` so they
match the pgvector column.
"""

from typing import List
import hashlib

from app.core.config import settings
from app.utils.retry import RetryableServiceError, with_retries

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None

try:
    from fastembed import TextEmbedding
except Exception:  # pragma: no cover
    TextEmbedding = None

_sentence_transformer = None
_fastembed_model = None


def _fastembed_embed(texts: List[str]):
    """Light ONNX build of all-MiniLM-L6-v2 (384-d, no PyTorch) for small servers."""
    global _fastembed_model
    if TextEmbedding is None:
        raise RuntimeError("fastembed is unavailable")
    if _fastembed_model is None:
        _fastembed_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return [v.tolist() for v in _fastembed_model.embed(texts)]


def _get_sentence_transformer():
    global _sentence_transformer
    if _sentence_transformer is None:
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers is unavailable")

        model_name = (settings.EMBEDDING_MODEL or "").strip()
        if model_name.startswith("sentence-transformers/"):
            model_name = model_name.split("/", 1)[1]
        if not model_name:
            model_name = "all-MiniLM-L6-v2"

        _sentence_transformer = SentenceTransformer(model_name)
    return _sentence_transformer


def _sentence_transformer_embed(texts: List[str]):
    model = _get_sentence_transformer()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() if hasattr(v, "tolist") else list(v) for v in vectors]


def _hash_embed(texts: List[str], dim: int | None = None):
    """Deterministic no-dependency fallback embeddings.

    This keeps the system operational when model downloads or external APIs are
    unavailable. Quality is lower than semantic embeddings and should be treated
    as an emergency fallback.
    """
    dim = dim or settings.EMBEDDING_DIM
    vectors = []
    for t in texts:
        data = (t or "").encode("utf-8", errors="ignore")
        digest = hashlib.sha256(data).digest()
        # Expand digest to requested dimension and map bytes to [-1, 1].
        expanded = (digest * ((dim // len(digest)) + 1))[:dim]
        vec = [((b / 255.0) * 2.0) - 1.0 for b in expanded]
        vectors.append(vec)
    return vectors


@with_retries(max_attempts=3)
def _gemini_embed(texts: List[str], for_query: bool = False):
    import google.generativeai as genai

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai.configure(api_key=settings.GEMINI_API_KEY)
    # Gemini embedding model name is separate from generation models.
    model = "text-embedding-004"
    task_type = "retrieval_query" if for_query else "retrieval_document"
    vectors = []
    for t in texts:
        try:
            resp = genai.embed_content(model=model, content=t, task_type=task_type)
        except Exception as e:
            msg = str(e).lower()
            if "429" in msg or "rate" in msg or "timeout" in msg or "temporar" in msg or "unavailable" in msg:
                raise RetryableServiceError(str(e)) from e
            raise
        vec = resp.get("embedding") if isinstance(resp, dict) else getattr(resp, "embedding", None)
        if not vec:
            raise RuntimeError("Gemini embedding returned empty vector")
        vectors.append(vec)
    return vectors


def embed_texts(texts: List[str], for_query: bool = False):
    if isinstance(texts, str):
        texts = [texts]

    # Gemini embeddings are 768-d, so they are only used if the column was migrated to 768.
    if settings.GEMINI_API_KEY and settings.EMBEDDING_DIM == 768:
        try:
            return _gemini_embed(texts, for_query=for_query)
        except Exception:
            pass

    # Local 384-d models: sentence-transformers if installed, else the light fastembed build.
    if settings.EMBEDDING_MODEL:
        for embed in (_sentence_transformer_embed, _fastembed_embed):
            try:
                return embed(texts)
            except Exception:
                continue

    return _hash_embed(texts)
