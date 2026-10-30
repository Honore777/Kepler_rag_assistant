"""Embedding service.

Provider is chosen by ``EMBEDDING_PROVIDER``:
- ``gemini``: Gemini API (gemini-embedding-001, truncated to EMBEDDING_DIM). No
  local model is loaded, so memory stays small. Failures raise; there is no
  silent fallback because mixed providers would corrupt the vector column.
- ``local`` (default): sentence-transformers if installed, else fastembed ONNX
  MiniLM, else a deterministic hash fallback (emergency only, low quality).

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

_sentence_transformer = None
_fastembed_model = None


def _fastembed_embed(texts: List[str]):
    """Light ONNX build of all-MiniLM-L6-v2 (384-d, no PyTorch) for small servers."""
    global _fastembed_model
    try:
        from fastembed import TextEmbedding
    except Exception as e:
        raise RuntimeError("fastembed is unavailable") from e
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


GEMINI_EMBED_MODEL = "gemini-embedding-001"
_GEMINI_BATCH = 50


@with_retries(max_attempts=5, min_wait_s=6.0, max_wait_s=40.0)
def _gemini_embed_batch(texts: List[str], task_type: str):
    """One batchEmbedContents call. Output is truncated to EMBEDDING_DIM and L2-normalised."""
    import json
    import math
    import urllib.error
    import urllib.request

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
    dim = settings.EMBEDDING_DIM
    body = json.dumps(
        {
            "requests": [
                {
                    "model": f"models/{GEMINI_EMBED_MODEL}",
                    "content": {"parts": [{"text": t}]},
                    "taskType": task_type,
                    "outputDimensionality": dim,
                }
                for t in texts
            ]
        }
    ).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_EMBED_MODEL}:batchEmbedContents",
        body,
        {"Content-Type": "application/json", "x-goog-api-key": settings.GEMINI_API_KEY},
    )
    try:
        data = json.load(urllib.request.urlopen(req, timeout=settings.LLM_TIMEOUT_S))
    except urllib.error.HTTPError as e:
        if e.code in (429, 500, 502, 503, 504):
            raise RetryableServiceError(f"Gemini embeddings HTTP {e.code}") from e
        raise RuntimeError(f"Gemini embeddings HTTP {e.code}: {e.read()[:200]!r}") from e

    vectors = []
    for item in data.get("embeddings", []):
        v = item.get("values") or []
        if len(v) != dim:
            raise RuntimeError(f"Gemini returned {len(v)}-d vector, expected {dim}")
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        vectors.append([x / norm for x in v])
    if len(vectors) != len(texts):
        raise RuntimeError("Gemini embeddings returned an unexpected number of vectors")
    return vectors


def _gemini_embed(texts: List[str], for_query: bool = False):
    task_type = "RETRIEVAL_QUERY" if for_query else "RETRIEVAL_DOCUMENT"
    vectors: List[List[float]] = []
    for i in range(0, len(texts), _GEMINI_BATCH):
        vectors.extend(_gemini_embed_batch(texts[i : i + _GEMINI_BATCH], task_type))
    return vectors


def embed_texts(texts: List[str], for_query: bool = False):
    if isinstance(texts, str):
        texts = [texts]

    # Gemini mode never falls back to a local model: mixing providers inside one
    # vector column silently ruins retrieval, so failures must surface.
    if (settings.EMBEDDING_PROVIDER or "local").lower().strip() == "gemini":
        return _gemini_embed(texts, for_query=for_query)

    # Local 384-d models: sentence-transformers if installed, else the light fastembed build.
    if settings.EMBEDDING_MODEL:
        for embed in (_sentence_transformer_embed, _fastembed_embed):
            try:
                return embed(texts)
            except Exception:
                continue

    return _hash_embed(texts)
