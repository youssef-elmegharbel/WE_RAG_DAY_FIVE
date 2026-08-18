import pytest


class FakeStore:
    """Stands in for Chroma; returns preloaded (Document, score) pairs."""

    def __init__(self, results):
        self.results = results
        self.last_query = None
        self.last_k = None

    def similarity_search_with_relevance_scores(self, query, k=5, **kwargs):
        self.last_query = query
        self.last_k = k
        return self.results[:k]


@pytest.fixture
def make_doc():
    from langchain_core.documents import Document

    def _make(text="Depth-first search expands the deepest node.", **overrides):
        metadata = {
            "chapter_num": 3,
            "chapter_title": "SOLVING PROBLEMS BY SEARCHING",
            "section": "3.4",
            "section_title": "Uninformed Search Strategies",
            "page_start": 84,
            "page_end": 84,
        }
        metadata.update(overrides)
        return Document(page_content=text, metadata=metadata)

    return _make
