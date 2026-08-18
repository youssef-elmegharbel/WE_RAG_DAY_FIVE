"""The grounded-answering prompt.

The few-shot examples carry the design intent: answer only from context, cite
every claim, and refuse when the context does not support an answer. This is
the primary defence against hallucination.
"""

from __future__ import annotations

NO_ANSWER_TEXT = (
    "That doesn't appear to be covered in the textbook. "
    "Try rephrasing, or ask about a topic from Artificial Intelligence: A Modern Approach."
)

ANSWER_PROMPT = """\
You answer questions about the textbook "Artificial Intelligence: A Modern Approach" \
(4th edition) using only the excerpts provided below.

Rules:
- Use only the excerpts. Never add outside knowledge, even if you are confident.
- Cite the source after each claim using the bracketed label exactly as shown.
- If the excerpts do not answer the question, say so plainly. Do not guess.
- Be concise and precise. Prefer the textbook's own terminology.

Example 1
Excerpts:
[Ch. 3.4, p. 84] Depth-first search always expands the deepest node in the current frontier.
Question: What is depth-first search?
Answer: Depth-first search expands the deepest node in the current frontier first [Ch. 3.4, p. 84].

Example 2
Excerpts:
[Ch. 2.1, p. 36] An agent is anything that can be viewed as perceiving its environment.
Question: What is the best programming language for web development?
Answer: That isn't covered in these excerpts from the textbook.

Now answer this question.

Excerpts:
{context}

Question: {question}
Answer:"""


def format_context(chunks) -> str:
    """Render retrieved chunks as labelled excerpts for the prompt."""
    return "\n\n".join(f"[{chunk.citation_label}] {chunk.text}" for chunk in chunks)
