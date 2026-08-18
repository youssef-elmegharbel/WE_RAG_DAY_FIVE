import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from rag.chain import ChatResult, Citation


@pytest.fixture
def client():
    return TestClient(create_app())


def make_result():
    return ChatResult(
        answer="DFS expands the deepest node [Ch. 3.4, p. 84].",
        citations=[
            Citation(
                label="Ch. 3.4, p. 84",
                chapter_num=3,
                chapter_title="SOLVING PROBLEMS BY SEARCHING",
                section="3.4",
                section_title="Uninformed Search Strategies",
                page_start=84,
                page_end=84,
                snippet="Depth-first search always expands the deepest node.",
            )
        ],
        rewritten_query="What is depth-first search?",
    )


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_returns_answer_and_citations(monkeypatch, client):
    monkeypatch.setattr("api.routes.answer_question", lambda **kw: make_result())

    response = client.post("/chat", json={"message": "What is DFS?", "history": []})

    assert response.status_code == 200
    body = response.json()
    assert "deepest node" in body["answer"]
    assert body["citations"][0]["label"] == "Ch. 3.4, p. 84"
    assert body["citations"][0]["snippet"]
    assert body["rewritten_query"] == "What is depth-first search?"


def test_chat_rejects_empty_message(client):
    response = client.post("/chat", json={"message": "   ", "history": []})

    assert response.status_code == 422


def test_chat_reports_missing_index_as_503(monkeypatch, client):
    from rag.retriever import IndexNotFoundError

    def explode(**kwargs):
        raise IndexNotFoundError("No index at data/index.")

    monkeypatch.setattr("api.routes.answer_question", explode)

    response = client.post("/chat", json={"message": "What is DFS?", "history": []})

    assert response.status_code == 503
    assert "ingest.build_index" in response.json()["detail"]


def test_chat_maps_rate_limit_to_429(monkeypatch, client):
    def explode(**kwargs):
        raise RuntimeError("429 Resource exhausted: quota exceeded")

    monkeypatch.setattr("api.routes.answer_question", explode)

    response = client.post("/chat", json={"message": "What is DFS?", "history": []})

    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()


def test_config_reports_active_provider(monkeypatch, client):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("LLM_MODEL", "gemini-2.0-flash")

    response = client.get("/config")

    assert response.status_code == 200
    assert response.json()["provider"] == "gemini"
    assert response.json()["model"] == "gemini-2.0-flash"
