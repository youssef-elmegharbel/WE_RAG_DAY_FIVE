import pytest

from rag.retriever import RetrievedChunk, retrieve
from tests.conftest import FakeStore


def test_returns_chunks_above_threshold(monkeypatch, make_doc):
    store = FakeStore([(make_doc(), 0.82), (make_doc(), 0.61)])
    monkeypatch.setattr("rag.retriever.get_store", lambda: store)

    results = retrieve("what is depth-first search", k=5, threshold=0.35)

    assert len(results) == 2
    assert results[0].score == 0.82
    assert results[0].chapter_num == 3


def test_filters_out_chunks_below_threshold(monkeypatch, make_doc):
    store = FakeStore([(make_doc(), 0.80), (make_doc(), 0.10)])
    monkeypatch.setattr("rag.retriever.get_store", lambda: store)

    results = retrieve("query", k=5, threshold=0.35)

    assert len(results) == 1


def test_returns_empty_when_nothing_is_relevant(monkeypatch, make_doc):
    """This is what triggers the 'not covered in the textbook' answer."""
    store = FakeStore([(make_doc(), 0.05)])
    monkeypatch.setattr("rag.retriever.get_store", lambda: store)

    assert retrieve("what is the capital of France", k=5, threshold=0.35) == []


def test_citation_label_formats_chapter_section_and_page():
    chunk = RetrievedChunk(
        text="...",
        score=0.9,
        chapter_num=3,
        chapter_title="SOLVING PROBLEMS BY SEARCHING",
        section="3.4",
        section_title="Uninformed Search Strategies",
        page_start=84,
        page_end=84,
    )

    assert chunk.citation_label == "Ch. 3.4, p. 84"


def test_citation_label_shows_page_range_when_chunk_spans_pages():
    chunk = RetrievedChunk(
        text="...",
        score=0.9,
        chapter_num=3,
        chapter_title="SOLVING PROBLEMS BY SEARCHING",
        section="3.4",
        section_title="Uninformed Search Strategies",
        page_start=84,
        page_end=86,
    )

    assert chunk.citation_label == "Ch. 3.4, pp. 84-86"
