from rag.rewrite import rewrite_query


class FakeLLM:
    def __init__(self, reply="What is iterative deepening search?"):
        self.reply = reply
        self.last_prompt = None

    def invoke(self, prompt):
        self.last_prompt = prompt

        class Result:
            content = self.reply

        return Result()


class ExplodingLLM:
    def invoke(self, prompt):
        raise RuntimeError("provider is down")


def test_returns_question_unchanged_when_history_is_empty():
    """No history means nothing to resolve; skip the LLM call entirely."""
    llm = FakeLLM()

    assert rewrite_query("What is A* search?", [], llm=llm) == "What is A* search?"
    assert llm.last_prompt is None


def test_rewrites_followup_using_history():
    llm = FakeLLM(reply="What is iterative deepening search?")
    history = [
        {"role": "user", "content": "What is depth-first search?"},
        {"role": "assistant", "content": "DFS expands the deepest node first."},
    ]

    result = rewrite_query("what about the iterative version?", history, llm=llm)

    assert result == "What is iterative deepening search?"
    assert "depth-first" in llm.last_prompt


def test_falls_back_to_raw_question_when_llm_fails():
    """Rewriting is an optimisation and must never break the request."""
    history = [{"role": "user", "content": "What is DFS?"}]

    result = rewrite_query("what about BFS?", history, llm=ExplodingLLM())

    assert result == "what about BFS?"


def test_falls_back_when_llm_returns_empty_output():
    history = [{"role": "user", "content": "What is DFS?"}]

    result = rewrite_query("what about BFS?", history, llm=FakeLLM(reply="   "))

    assert result == "what about BFS?"
