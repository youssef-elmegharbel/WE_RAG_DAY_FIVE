import pytest

from ingest.parse import (
    ParsedPage,
    detect_heading,
    line_texts,
)
from ingest.parse import detect_chapter_start, detect_page_offset, printed_page_from_lines


def make_page_dict(lines):
    """Build a minimal PyMuPDF 'dict' structure from (text, size, font) spans."""
    return {
        "blocks": [
            {
                "lines": [
                    {"spans": [{"text": t, "size": s, "font": f} for (t, s, f) in spans]}
                    for spans in lines
                ]
            }
        ]
    }


def test_line_texts_joins_word_level_spans():
    page = make_page_dict([
        [("1.3", 14.3, "CMSSBX10"), ("The", 14.3, "CMSSBX10"),
         ("History", 14.3, "CMSSBX10"), ("of", 14.3, "CMSSBX10"),
         ("AI", 14.3, "CMSSBX10")],
    ])

    lines = line_texts(page)

    assert lines == [("1.3 The History of AI", 14.3, "CMSSBX10")]


def test_detect_heading_recognises_section():
    heading = detect_heading("1.3 The History of AI", 14.3, "CMSSBX10")

    assert heading == ("section", "1.3", "The History of AI")


def test_detect_heading_recognises_subsection():
    heading = detect_heading("1.3.1 The inception (1943-1956)", 12.0, "CMSSBX10")

    assert heading == ("section", "1.3.1", "The inception (1943-1956)")


def test_detect_heading_ignores_body_text():
    assert detect_heading("The Turing test was proposed in 1950.", 10.9, "NimbusRomNo9L") is None


def test_detect_heading_ignores_unnumbered_large_text():
    """Decorative glyphs and running heads are large but not numbered headings."""
    assert detect_heading("Section 1.3", 10.0, "CMSSBX10") is None
    assert detect_heading("◭", 24.8, "CMSY10") is None


def test_detect_chapter_start_reads_number_and_title():
    lines = [
        ("CHAPTER", 26.0, "CMSSBX10"),
        ("2", 59.8, "CMSSBX10"),
        ("INTELLIGENT AGENTS", 26.9, "CMSSBX10"),
        ("In which we discuss agents.", 10.9, "NimbusRomNo9L"),
    ]

    assert detect_chapter_start(lines) == (2, "INTELLIGENT AGENTS")


def test_detect_chapter_start_returns_none_for_body_page():
    lines = [("The Turing test was proposed in 1950.", 10.9, "NimbusRomNo9L")]

    assert detect_chapter_start(lines) is None


def test_detect_chapter_start_ignores_decorative_glyphs():
    """Large glyphs appear throughout the book but are not chapter starts."""
    lines = [("◮", 24.8, "CMSY10"), ("body text here", 10.9, "NimbusRomNo9L")]

    assert detect_chapter_start(lines) is None


def test_printed_page_from_lines_reads_leading_number():
    lines = [("18", 10.0, "NimbusRomNo9L"), ("Chapter 1", 10.0, "NimbusRomNo9L")]

    assert printed_page_from_lines(lines) == 18


def test_printed_page_from_lines_returns_none_when_absent():
    lines = [("Section 1.3", 10.0, "NimbusRomNo9L")]

    assert printed_page_from_lines(lines) is None


class FakePage:
    def __init__(self, page_dict):
        self._page_dict = page_dict

    def get_text(self, kind):
        assert kind == "dict"
        return self._page_dict


class FakeDoc:
    """Minimal stand-in for a pymupdf.Document, indexable and sized."""

    def __init__(self, pages):
        self._pages = [FakePage(p) for p in pages]
        self.page_count = len(self._pages)

    def __getitem__(self, index):
        return self._pages[index]


def test_detect_page_offset_uses_median_of_printed_numbers():
    # PDF index 0 -> printed "1" (offset -1), index 1 -> printed "2" (offset -1),
    # index 2 -> printed "50" (a misread outlier, offset -48). Median wins.
    pages = [
        make_page_dict([[("1", 10.0, "NimbusRomNo9L")]]),
        make_page_dict([[("2", 10.0, "NimbusRomNo9L")]]),
        make_page_dict([[("50", 10.0, "NimbusRomNo9L")]]),
    ]
    doc = FakeDoc(pages)

    assert detect_page_offset(doc) == -1


def test_detect_page_offset_raises_when_no_page_numbers_found():
    pages = [make_page_dict([[("Section 1.3", 10.0, "NimbusRomNo9L")]])]
    doc = FakeDoc(pages)

    with pytest.raises(ValueError):
        detect_page_offset(doc)
