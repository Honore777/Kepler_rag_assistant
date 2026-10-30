"""Answer synthesis service.

This service is responsible for turning retrieved context into a final answer.

- `extractive` mode: returns top passages (no external API).
- `gemini` mode: calls Gemini with retries and falls back to extractive.
"""

from typing import List

from app.core.config import settings
from app.utils.retry import RetryableServiceError, with_retries


def _extractive_answer(question: str, passages: List[str]) -> str:
    assembled = "\n\n".join([p for p in passages if p])
    if not assembled:
        return "I couldn't find relevant information in the active documents."
    if len(assembled) > 2000:
        assembled = assembled[:2000] + "..."
    return assembled


@with_retries(max_attempts=3)
def _gemini_generate(prompt: str) -> str:
    import google.generativeai as genai

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    try:
        resp = model.generate_content(prompt)
    except Exception as e:
        msg = str(e).lower()
        if "429" in msg or "rate" in msg or "timeout" in msg or "temporar" in msg or "unavailable" in msg:
            raise RetryableServiceError(str(e)) from e
        raise
    text = getattr(resp, "text", None)
    if not text:
        raise RuntimeError("Gemini returned empty response")
    return text


@with_retries(max_attempts=3)
def _groq_generate(prompt: str) -> str:
    """Generate via Groq Chat Completions."""
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")

    try:
        from groq import Groq
    except Exception as e:
        raise RuntimeError(f"groq package not installed: {e}")

    client = Groq(api_key=settings.GROQ_API_KEY)
    model = settings.GROQ_MODEL
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the official Kepler College assistant for students and staff. "
                        "Answer using ONLY the provided context. "
                        "If the context does not contain the answer, say you don't know and suggest where to look."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
    except Exception as e:
        msg = str(e).lower()
        if "429" in msg or "rate" in msg or "timeout" in msg or "temporar" in msg or "unavailable" in msg:
            raise RetryableServiceError(str(e)) from e
        raise
    content = resp.choices[0].message.content if resp and resp.choices else None
    if not content:
        raise RuntimeError("Groq returned empty response")
    return content


def generate_answer(question: str, passages: List[str], history: List[str] | None = None) -> str:
    provider = (settings.LLM_PROVIDER or "extractive").lower().strip()
    history_block = ""
    if history:
        compact_history = [h.strip() for h in history if isinstance(h, str) and h.strip()]
        if compact_history:
            history_block = "Conversation history (most recent first):\n" + "\n".join(compact_history[:8]) + "\n\n"

    prompt = (
        history_block
        + f"Question:\n{question}\n\n"
        "Context (retrieved passages):\n" + "\n\n---\n\n".join(passages[:8])
    )

    # If provider explicitly requested, honor it.
    if provider == "groq":
        try:
            return _groq_generate(prompt)
        except Exception:
            if settings.GEMINI_API_KEY:
                try:
                    return _gemini_generate(prompt)
                except Exception:
                    return _extractive_answer(question, passages)
            return _extractive_answer(question, passages)

    if provider == "gemini":
        try:
            return _gemini_generate(prompt)
        except Exception:
            if settings.GROQ_API_KEY:
                try:
                    return _groq_generate(prompt)
                except Exception:
                    return _extractive_answer(question, passages)
            return _extractive_answer(question, passages)

    # Auto mode: Groq -> Gemini -> extractive
    if provider in ("auto", ""):
        if settings.GROQ_API_KEY:
            try:
                return _groq_generate(prompt)
            except Exception:
                pass
        if settings.GEMINI_API_KEY:
            try:
                return _gemini_generate(prompt)
            except Exception:
                pass
        return _extractive_answer(question, passages)

    # extractive (or unknown)
    return _extractive_answer(question, passages)
