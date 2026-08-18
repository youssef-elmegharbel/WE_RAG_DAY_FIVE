import pytest

from ingest.parse import (
    ParsedPage,
    detect_heading,
    line_texts,
    parse_page_dict,
)


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
