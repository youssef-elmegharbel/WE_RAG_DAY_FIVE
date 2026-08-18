"""Parse the AIMA PDF into pages carrying chapter and section metadata.

The PDF has no embedded table of contents, so structure is recovered from font
analysis. Verified characteristics of this book:

  - body text            10.9pt
  - section headings     14.3pt, font CMSSBX10, numbered "N.M"
  - subsection headings  12.0pt, font CMSSBX10, numbered "N.M.K"
  - chapter start pages  contain a ~59.8pt joined line "CHAPTER N" (font NimbusSanL-ReguCond),
                         followed by the chapter title at 26.9pt

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


CHAPTER_NUMBER_SIZE = 59.8
CHAPTER_TITLE_SIZE = 26.9
CHAPTER_NUMBER_RE = re.compile(r"^(?:CHAPTER\s+)?(\d+)$", re.IGNORECASE)


def detect_chapter_start(lines: list[tuple[str, float, str]]) -> tuple[int, str] | None:
    """Return (chapter_number, title) when the page opens a chapter.

    A chapter-start page carries a ~59.8pt line giving the chapter number
    (either "CHAPTER N" joined on one line, or a bare "N", depending on how
    the PDF's spans happen to be grouped), immediately followed by the
    chapter title at ~26.9pt (possibly wrapped across multiple lines, as with
    two-line appendix titles). "APPENDIX" pages use the same 59.8pt styling
    but are excluded here since they are not numbered chapters.
    """
    number: int | None = None
    number_idx: int | None = None
    for idx, (text, size, _) in enumerate(lines):
        if abs(size - CHAPTER_NUMBER_SIZE) < 1.0:
            match = CHAPTER_NUMBER_RE.match(text.strip())
            if match:
                number = int(match.group(1))
                number_idx = idx
                break
    if number is None:
        return None

    title_parts: list[str] = []
    for text, size, _ in lines[number_idx + 1 :]:
        if abs(size - CHAPTER_TITLE_SIZE) < SIZE_TOLERANCE:
            title_parts.append(text.strip())
        elif title_parts:
            break
        else:
            break
    if not title_parts:
        return None
    title = " ".join(title_parts)
    if not CHAPTER_TITLE_RE.match(title):
        return None
    return (number, title)


def printed_page_from_lines(lines: list[tuple[str, float, str]]) -> int | None:
    """Read the printed page number, which appears as a bare number in the header."""
    for text, _, _ in lines[:3]:
        stripped = text.strip()
        if stripped.isdigit() and len(stripped) <= 4:
            return int(stripped)
    return None


def detect_page_offset(doc: "pymupdf.Document") -> int:
    """Discover the offset between PDF index and printed page number.

    Uses the median of all pages where a printed number is visible, so a few
    misreads cannot skew the result.
    """
    offsets: list[int] = []
    for index in range(min(doc.page_count, 400)):
        lines = line_texts(doc[index].get_text("dict"))
        printed = printed_page_from_lines(lines)
        if printed is not None and printed > 0:
            offsets.append(index - printed)
    if not offsets:
        raise ValueError("Could not determine printed-page offset; no page numbers found.")
    offsets.sort()
    return offsets[len(offsets) // 2]


def parse_pdf(pdf_path: Path) -> list[ParsedPage]:
    """Parse the whole book, carrying chapter and section state across pages."""
    doc = pymupdf.open(pdf_path)
    offset = detect_page_offset(doc)

    pages: list[ParsedPage] = []
    chapter_num: int | None = None
    chapter_title: str | None = None
    section: str | None = None
    section_title: str | None = None

    for index in range(doc.page_count):
        page = doc[index]
        lines = line_texts(page.get_text("dict"))
        if not lines:
            continue

        chapter = detect_chapter_start(lines)
        if chapter is not None:
            chapter_num, chapter_title = chapter
            section, section_title = None, None

        for text, size, font in lines:
            heading = detect_heading(text, size, font)
            if heading is not None:
                _, section, section_title = heading

        text = page.get_text().strip()
        if not text:
            continue

        pages.append(
            ParsedPage(
                text=text,
                pdf_index=index,
                printed_page=index - offset,
                chapter_num=chapter_num,
                chapter_title=chapter_title,
                section=section,
                section_title=section_title,
            )
        )

    doc.close()
    return pages
