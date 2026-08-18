"""Parse the AIMA PDF into pages carrying chapter and section metadata.

The PDF has no embedded table of contents, so structure is recovered from font
analysis. Verified characteristics of this book:

  - body text            10.9pt
  - section headings     14.3pt, font CMSSBX10, numbered "N.M"
  - subsection headings  12.0pt, font CMSSBX10, numbered "N.M.K"
  - chapter start pages  contain a 26.0pt "CHAPTER" span and a 59.8pt number

PyMuPDF returns heading text as word-level spans, so spans must be joined per
line before any pattern matching.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf

HEADING_FONT = "CMSSBX10"
SECTION_SIZE = 14.3
SUBSECTION_SIZE = 12.0
SIZE_TOLERANCE = 0.3

SECTION_RE = re.compile(r"^(\d+\.\d+(?:\.\d+)?)\s+(\S.*)$")
CHAPTER_TITLE_RE = re.compile(r"^[A-Z][A-Z\s,'\-:]{3,}$")


@dataclass
class ParsedPage:
    text: str
    pdf_index: int
    printed_page: int | None
    chapter_num: int | None
    chapter_title: str | None
    section: str | None
    section_title: str | None


def line_texts(page_dict: dict) -> list[tuple[str, float, str]]:
    """Join word-level spans into whole lines.

    Returns one tuple per line: (joined text, largest span size, font of the
    largest span).
    """
    lines: list[tuple[str, float, str]] = []
    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            spans = [s for s in line.get("spans", []) if s.get("text", "").strip()]
            if not spans:
                continue
            text = " ".join(s["text"].strip() for s in spans)
            largest = max(spans, key=lambda s: s["size"])
            lines.append((re.sub(r"\s+", " ", text).strip(), largest["size"], largest["font"]))
    return lines


def detect_heading(text: str, size: float, font: str) -> tuple[str, str, str] | None:
    """Return ("section", number, title) when the line is a numbered heading."""
    if HEADING_FONT not in font:
        return None
    is_section = abs(size - SECTION_SIZE) < SIZE_TOLERANCE
    is_subsection = abs(size - SUBSECTION_SIZE) < SIZE_TOLERANCE
    if not (is_section or is_subsection):
        return None
    match = SECTION_RE.match(text)
    if not match:
        return None
    return ("section", match.group(1), match.group(2).strip())


def parse_page_dict(page_dict: dict) -> ParsedPage:
    """Placeholder for parse_page_dict - will be implemented in Task 3."""
    pass
