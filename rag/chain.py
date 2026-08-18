"""Wire the pipeline: rewrite -> retrieve -> grounded prompt -> generate."""

from __future__ import annotations

from dataclasses import dataclass, field

from rag.prompts import ANSWER_PROMPT, NO_ANSWER_TEXT, format_context
from rag.providers import get_llm
from rag.retriever import RetrievedChunk, retrieve
from rag.rewrite import rewrite_query

SNIPPET_CHARS = 400


@dataclass
class Citation:
    label: str
    chapter_num: int
    chapter_title: str
    section: str
    section_title: str
    page_start: int
    page_end: int
    snippet: str


@dataclass
class ChatResult:
    answer: str
    citations: list[Citation] = field(default_factory=list)
    rewritten_query: str = ""


def _to_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    """Convert chunks to citations, keeping the first occurrence of each label."""
    seen: set[str] = set()
    citations: list[Citation] = []
    for chunk in chunks:
        if chunk.citation_label in seen:
            continue
        seen.add(chunk.citation_label)
        citations.append(
            Citation(
                label=chunk.citation_label,
                chapter_num=chunk.chapter_num,
                chapter_title=chunk.chapter_title,
                section=chunk.section,
                section_title=chunk.section_title,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                snippet=chunk.text[:SNIPPET_CHARS],
            )
        )
    return citations


def answer_question(
    question: str,
    history: list[dict] | None = None,
    llm=None,
) -> ChatResult:
    """Answer a question using only textbook content."""
    history = history or []
    llm = llm or get_llm()

    query = rewrite_query(question, history, llm=llm)
    chunks = retrieve(query)

    if not chunks:
        return ChatResult(answer=NO_ANSWER_TEXT, citations=[], rewritten_query=query)

    prompt = ANSWER_PROMPT.format(context=format_context(chunks), question=question)
    answer = llm.invoke(prompt).content.strip()

    return ChatResult(
        answer=answer,
        citations=_to_citations(chunks),
        rewritten_query=query,
    )
