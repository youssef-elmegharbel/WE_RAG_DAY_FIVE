import pytest

from rag.chain import answer_question
from rag.prompts import NO_ANSWER_TEXT, format_context
from rag.retriever import RetrievedChunk


class FakeLLM:
    def __init__(self, reply="Depth-first search expands the deepest node first."):
        self.reply = reply
        self.last_prompt = None

    def invoke(self, prompt):
        self.last_prompt = prompt

        class Result:
            content = self.reply

        return Result()


def make_chunk(**overrides):
    fields = {
        "text": "Depth-first search always expands the deepest node.",
        "score": 0.9,
        "chapter_num": 3,
        "chapter_title": "SOLVING PROBLEMS BY SEARCHING",
        "section": "3.4",
        "section_title": "Uninformed Search Strategies",
        "page_start": 84,
        "page_end": 84,
    }
    fields.update(overrides)
    return RetrievedChunk(**fields)


def test_returns_answer_with_citations(monkeypatch):
    monkeypatch.setattr("rag.chain.retrieve", lambda q, **kw: [make_chunk()])
    llm = FakeLLM()

    result = answer_question("What is depth-first search?", llm=llm)

    assert "deepest node" in result.answer
    assert len(result.citations) == 1
    assert result.citations[0].label == "Ch. 3.4, p. 84"
    assert result.citations[0].snippet


def test_skips_llm_entirely_when_nothing_is_retrieved(monkeypatch):
    """No relevant context means no LLM call - cheaper and more honest."""
    monkeypatch.setattr("rag.chain.retrieve", lambda q, **kw: [])
    llm = FakeLLM()

    result = answer_question("What is the capital of France?", llm=llm)

    assert result.answer == NO_ANSWER_TEXT
    assert result.citations == []
    assert llm.last_prompt is None


def test_retrieved_context_is_passed_into_the_prompt(monkeypatch):
    monkeypatch.setattr("rag.chain.retrieve", lambda q, **kw: [make_chunk()])
    llm = FakeLLM()

    answer_question("What is depth-first search?", llm=llm)

    assert "deepest node" in llm.last_prompt
    assert "Ch. 3.4, p. 84" in llm.last_prompt


def test_uses_rewritten_query_for_retrieval(monkeypatch):
    seen = {}

    def fake_retrieve(query, **kwargs):
        seen["query"] = query
        return [make_chunk()]

    monkeypatch.setattr("rag.chain.retrieve", fake_retrieve)
    monkeypatch.setattr("rag.chain.rewrite_query", lambda q, h, llm=None: "standalone query")

    result = answer_question("what about it?", history=[{"role": "user", "content": "DFS?"}], llm=FakeLLM())

    assert seen["query"] == "standalone query"
    assert result.rewritten_query == "standalone query"


def test_citations_are_deduplicated_by_label(monkeypatch):
    monkeypatch.setattr(
        "rag.chain.retrieve",
        lambda q, **kw: [make_chunk(), make_chunk(text="More on DFS.")],
    )

    result = answer_question("What is depth-first search?", llm=FakeLLM())

    assert len(result.citations) == 1


def test_format_context_labels_each_source():
    context = format_context([make_chunk()])

    assert "[Ch. 3.4, p. 84]" in context
    assert "deepest node" in context
