from ingest.chunk import chunk_pages
from ingest.parse import ParsedPage


def make_page(text, printed_page=10, chapter_num=3, section="3.1"):
    return ParsedPage(
        text=text,
        pdf_index=printed_page + 12,
        printed_page=printed_page,
        chapter_num=chapter_num,
        chapter_title="SOLVING PROBLEMS BY SEARCHING",
        section=section,
        section_title="Problem-Solving Agents",
    )


def test_chunks_never_span_two_sections():
    pages = [
        make_page("alpha " * 200, printed_page=10, section="3.1"),
        make_page("beta " * 200, printed_page=11, section="3.2"),
    ]

    chunks = chunk_pages(pages, chunk_size=1000, overlap=200)

    for chunk in chunks:
        assert "alpha" not in chunk.text or "beta" not in chunk.text


def test_every_chunk_carries_complete_metadata():
    chunks = chunk_pages([make_page("word " * 400)], chunk_size=500, overlap=100)

    assert chunks
    for chunk in chunks:
        assert chunk.metadata["chapter_num"] == 3
        assert chunk.metadata["chapter_title"] == "SOLVING PROBLEMS BY SEARCHING"
        assert chunk.metadata["section"] == "3.1"
        assert chunk.metadata["page_start"] == 10
        assert chunk.metadata["page_end"] == 10


def test_page_range_spans_merged_pages_of_same_section():
    pages = [
        make_page("alpha " * 100, printed_page=10, section="3.1"),
        make_page("gamma " * 100, printed_page=11, section="3.1"),
    ]

    chunks = chunk_pages(pages, chunk_size=5000, overlap=100)

    assert len(chunks) == 1
    assert chunks[0].metadata["page_start"] == 10
    assert chunks[0].metadata["page_end"] == 11


def test_long_section_splits_into_multiple_chunks_with_overlap():
    chunks = chunk_pages([make_page("word " * 600)], chunk_size=500, overlap=100)

    assert len(chunks) > 1
    assert all(len(c.text) <= 500 for c in chunks)

    # Overlap check: the tail of each chunk should reappear at the head of the
    # next chunk, proving the splitter actually repeats content across the
    # boundary rather than just cutting the text into disjoint pieces.
    for first, second in zip(chunks, chunks[1:]):
        tail = first.text[-50:].strip()
        assert tail and tail in second.text


def test_pages_without_chapter_are_skipped():
    """Front matter has no chapter and must not pollute the index."""
    page = make_page("preface text", chapter_num=None)

    assert chunk_pages([page]) == []
