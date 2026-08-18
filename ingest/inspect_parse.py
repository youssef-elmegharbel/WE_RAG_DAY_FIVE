"""Manual spot-check of parser output. Not a test - run it and read the output."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from ingest.parse import parse_pdf
from rag.config import get_settings


def main() -> None:
    settings = get_settings()
    pdfs = sorted(Path(settings.pdf_path).glob("*.pdf"))
    if not pdfs:
        sys.exit(f"No PDF found in {settings.pdf_path}")

    pages = parse_pdf(pdfs[0])
    chapters = Counter(p.chapter_num for p in pages if p.chapter_num is not None)
    sections = {p.section for p in pages if p.section}

    print(f"parsed pages     : {len(pages)}")
    print(f"chapters found   : {len(chapters)} -> {sorted(chapters)}")
    print(f"distinct sections: {len(sections)}")
    print(f"pages w/o chapter: {sum(1 for p in pages if p.chapter_num is None)}")

    print("\n--- sample pages ---")
    for page in pages[100:103]:
        print(
            f"[pdf {page.pdf_index} | printed {page.printed_page}] "
            f"ch {page.chapter_num} {page.chapter_title!r} "
            f"sec {page.section} {page.section_title!r}"
        )
        print(page.text[:200].replace("\n", " "), "\n")


if __name__ == "__main__":
    main()
