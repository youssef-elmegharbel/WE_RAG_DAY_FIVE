"""Environment-driven settings shared by ingest, RAG core, and API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    pdf_path: Path
    index_dir: Path
    collection_name: str
    embedding_model: str
    top_k: int
    score_threshold: float


def get_settings() -> Settings:
    """Build settings from environment variables, falling back to defaults."""
    return Settings(
        provider=os.getenv("LLM_PROVIDER", "gemini"),
        model=os.getenv("LLM_MODEL", "gemini-2.0-flash"),
        pdf_path=Path(os.getenv("PDF_PATH", PROJECT_ROOT / "Textbook")),
        index_dir=Path(os.getenv("INDEX_DIR", PROJECT_ROOT / "data" / "index")),
        collection_name=os.getenv("COLLECTION_NAME", "aima"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
        top_k=int(os.getenv("TOP_K", "5")),
        score_threshold=float(os.getenv("SCORE_THRESHOLD", "0.35")),
    )
