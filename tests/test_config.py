import os
from pathlib import Path

from rag.config import Settings, get_settings


def test_defaults_when_env_empty(monkeypatch):
    for key in ("LLM_PROVIDER", "LLM_MODEL", "TOP_K", "SCORE_THRESHOLD"):
        monkeypatch.delenv(key, raising=False)

    settings = get_settings()

    assert settings.provider == "gemini"
    assert settings.model == "gemini-2.0-flash"
    assert settings.top_k == 5
    assert settings.embedding_model == "BAAI/bge-small-en-v1.5"
    assert isinstance(settings.index_dir, Path)


def test_env_overrides_defaults(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("TOP_K", "8")

    settings = get_settings()

    assert settings.provider == "openai"
    assert settings.model == "gpt-4o-mini"
    assert settings.top_k == 8
