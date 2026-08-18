"""Vector search over the persisted Chroma index."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from langchain_chroma import Chroma

from rag.config import get_settings
from rag.embeddings import get_embeddings


class IndexNotFoundError(RuntimeError):
    """Raised when the Chroma index has not been built yet."""


@dataclass
class RetrievedChunk:
    text: str
    score: float
    chapter_num: int
    chapter_title: str
    section: str
    section_title: str
    page_start: int
    page_end: int

    @property
    def citation_label(self) -> str:
        location = self.section or str(self.chapter_num)
        if self.page_start == self.page_end:
            return f"Ch. {location}, p. {self.page_start}"
        return f"Ch. {location}, pp. {self.page_start}-{self.page_end}"


@lru_cache(maxsize=1)
def get_store() -> Chroma:
    """Open the persisted index, failing loudly if it has not been built."""
    settings = get_settings()
    if not settings.index_dir.exists():
        raise IndexNotFoundError(
            f"No index at {settings.index_dir}. "
            "Build it first with: python -m ingest.build_index"
        )
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(settings.index_dir),
    )


def retrieve(
    query: str,
    k: int | None = None,
    threshold: float | None = None,
) -> list[RetrievedChunk]:
    """Return the top-k chunks scoring above the relevance threshold."""
    settings = get_settings()
    k = k if k is not None else settings.top_k
    threshold = threshold if threshold is not None else settings.score_threshold

    pairs = get_store().similarity_search_with_relevance_scores(query, k=k)

    results: list[RetrievedChunk] = []
    for document, score in pairs:
        if score < threshold:
            continue
        metadata = document.metadata
        results.append(
            RetrievedChunk(
                text=document.page_content,
                score=score,
                chapter_num=int(metadata.get("chapter_num", 0)),
                chapter_title=metadata.get("chapter_title", ""),
                section=metadata.get("section", ""),
                section_title=metadata.get("section_title", ""),
                page_start=int(metadata.get("page_start", 0)),
                page_end=int(metadata.get("page_end", 0)),
            )
        )
    return results
