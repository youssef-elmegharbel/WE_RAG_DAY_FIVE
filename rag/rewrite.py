"""Rewrite follow-up questions into standalone search queries.

Without this, a question like "explain that further" retrieves nothing useful
because it carries no searchable terms. Failure here is never fatal: the raw
question is used instead.
"""

from __future__ import annotations

import logging

from rag.providers import get_llm

logger = logging.getLogger(__name__)

REWRITE_PROMPT = """\
Rewrite the user's latest question into a single standalone search query for a \
textbook search engine.

Rules:
- Resolve pronouns and vague references using the conversation.
- Expand abbreviations where the conversation makes them clear.
- Keep technical terms exactly as written.
- Output only the rewritten query. No preamble, no quotes, no explanation.

Conversation:
{history}

Latest question: {question}

Standalone query:"""

MAX_HISTORY_TURNS = 6


def _format_history(history: list[dict]) -> str:
    recent = history[-MAX_HISTORY_TURNS:]
    return "\n".join(f"{turn['role']}: {turn['content']}" for turn in recent)


def rewrite_query(question: str, history: list[dict], llm=None) -> str:
    """Return a standalone query, falling back to the raw question on any failure."""
    if not history:
        return question

    try:
        llm = llm or get_llm()
        prompt = REWRITE_PROMPT.format(
            history=_format_history(history),
            question=question,
        )
        rewritten = llm.invoke(prompt).content.strip()
        if not rewritten:
            logger.warning("Query rewrite returned empty output; using raw question.")
            return question
        return rewritten
    except Exception:
        logger.warning("Query rewrite failed; using raw question.", exc_info=True)
        return question
