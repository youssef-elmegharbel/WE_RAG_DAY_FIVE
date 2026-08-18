"""Group parsed pages by section, then split each section into overlapping chunks."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import groupby

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ingest.parse import ParsedPage


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


def chunk_pages(
    pages: list[ParsedPage],
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[Chunk]:
    """Split pages into chunks that never cross a section boundary.

    Pages with no detected chapter (front and back matter) are discarded.
    """
    usable = [p for p in pages if p.chapter_num is not None]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[Chunk] = []
    key = lambda p: (p.chapter_num, p.section)  # noqa: E731

    for (chapter_num, section), group in groupby(usable, key=key):
        group_pages = list(group)
        text = "\n".join(p.text for p in group_pages)
        first = group_pages[0]
        page_numbers = [p.printed_page for p in group_pages if p.printed_page is not None]

        for piece in splitter.split_text(text):
            if not piece.strip():
                continue
            chunks.append(
                Chunk(
                    text=piece,
                    metadata={
                        "chapter_num": chapter_num,
                        "chapter_title": first.chapter_title or "",
                        "section": section or "",
                        "section_title": first.section_title or "",
                        "page_start": min(page_numbers) if page_numbers else 0,
                        "page_end": max(page_numbers) if page_numbers else 0,
                    },
                )
            )
    return chunks
