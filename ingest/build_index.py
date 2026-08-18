"""Build the Chroma index from the textbook PDF. Run once, offline."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from ingest.chunk import chunk_pages
from ingest.parse import parse_pdf
from rag.config import get_settings
from rag.embeddings import get_embeddings

BATCH_SIZE = 256


def build() -> int:
    settings = get_settings()
    pdfs = sorted(Path(settings.pdf_path).glob("*.pdf"))
    if not pdfs:
        sys.exit(
            f"No PDF found in {settings.pdf_path}. "
            "Place the textbook PDF there (see README) and retry."
        )

    print(f"parsing {pdfs[0].name} ...")
    pages = parse_pdf(pdfs[0])
    if not pages:
        sys.exit("Parsing produced no pages. Run `python -m ingest.inspect_parse` to diagnose.")

    chunks = chunk_pages(pages)
    if not chunks:
        sys.exit("Chunking produced no chunks. Check that chapters were detected.")

    chapters = {c.metadata["chapter_num"] for c in chunks}
    print(f"parsed {len(pages)} pages -> {len(chunks)} chunks across {len(chapters)} chapters")

    if settings.index_dir.exists():
        print(f"removing existing index at {settings.index_dir}")
        shutil.rmtree(settings.index_dir)
    settings.index_dir.mkdir(parents=True, exist_ok=True)

    store = Chroma(
        collection_name=settings.collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(settings.index_dir),
    )

    documents = [Document(page_content=c.text, metadata=c.metadata) for c in chunks]
    for start in range(0, len(documents), BATCH_SIZE):
        batch = documents[start : start + BATCH_SIZE]
        store.add_documents(batch)
        print(f"  embedded {min(start + BATCH_SIZE, len(documents))}/{len(documents)}")

    print(f"index written to {settings.index_dir}")
    return len(chunks)


if __name__ == "__main__":
    build()
