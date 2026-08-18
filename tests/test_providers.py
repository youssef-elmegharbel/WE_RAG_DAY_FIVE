import pytest

from rag.providers import UnknownProviderError, get_llm


def test_unknown_provider_raises_with_helpful_message():
    with pytest.raises(UnknownProviderError) as excinfo:
        get_llm("llama-on-a-toaster")

    message = str(excinfo.value)
    assert "llama-on-a-toaster" in message
    assert "gemini" in message


def test_gemini_provider_returns_google_chat_model(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    llm = get_llm("gemini", "gemini-2.0-flash")

    assert type(llm).__name__ == "ChatGoogleGenerativeAI"


def test_openai_provider_returns_openai_chat_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    llm = get_llm("openai", "gpt-4o-mini")

    assert type(llm).__name__ == "ChatOpenAI"


def test_ollama_provider_returns_ollama_chat_model():
    llm = get_llm("ollama", "llama3.1")

    assert type(llm).__name__ == "ChatOllama"


def test_defaults_come_from_settings(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_MODEL", "mistral")

    llm = get_llm()

    assert type(llm).__name__ == "ChatOllama"
