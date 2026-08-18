"""The only module that knows about specific LLM vendors.

Swapping providers is a configuration change; no other module imports a
provider SDK.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from rag.config import get_settings

SUPPORTED = ("gemini", "openai", "ollama")


class UnknownProviderError(ValueError):
    """Raised when the configured provider name is not recognised."""


def get_llm(provider: str | None = None, model: str | None = None) -> BaseChatModel:
    """Build a chat model for the given provider, defaulting to settings."""
    settings = get_settings()
    provider = (provider or settings.provider).lower()
    model = model or settings.model

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=model, temperature=0)

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model, temperature=0)

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=model, temperature=0)

    raise UnknownProviderError(
        f"Unknown provider {provider!r}. Supported providers: {', '.join(SUPPORTED)}."
    )
