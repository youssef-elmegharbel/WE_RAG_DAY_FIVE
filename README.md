# AIMA Textbook Assistant

A retrieval-augmented question-answering system over *Artificial Intelligence: A Modern
Approach* (4th ed., Russell & Norvig). Ask a question in natural language; get an answer
drawn only from the textbook, with citations to the chapter, section, and page.

## Why it's interesting

- **Structure-aware chunking.** The PDF ships no table of contents, so chapter and
  section boundaries are recovered from font analysis. Chunks never span sections, which
  is what makes citations like "Ch. 3.4, p. 84" precise enough to look up.
- **Grounded answering.** The prompt supplies labelled excerpts and few-shot examples
  covering both the citation format and the refusal case. Questions the textbook doesn't
  cover are refused rather than answered from model memory.
- **Query rewriting.** Follow-up questions ("what about the breadth-first version?") are
  rewritten into standalone search queries before retrieval.
- **Swappable providers.** Gemini, OpenAI, or a local model via Ollama, selected by one
  environment variable. Embeddings run locally, so the index is built once with no API
  key and works offline.
- **Measured, not asserted.** A 22-question evaluation set reports retrieval hit-rate,
  including out-of-scope questions that must be refused.

## Results

| Metric | Value |
|---|---|
| Retrieval hit-rate @5 | 81.8% (18/22), from `python -m eval.run_eval` |
| Chunks indexed | 4792, from `python -m ingest.build_index` |
| Chapters detected | 28 |

## Architecture

```
React SPA  ──HTTP──►  FastAPI  ──►  RAG core (LangChain)
                                      rewrite → retrieve → prompt → generate
                                         │              │
                                    Chroma index    LLM provider
                                    (local embeds)  (Gemini/OpenAI/Ollama)
```

## Setup

The textbook PDF is **not** included — it is copyrighted. Supply your own copy.

```bash
git clone <repo-url>
cd WE_RAG_DAY_FIVE

python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

mkdir Textbook                 # place the AIMA 4th ed. PDF here
cp .env.example .env           # add your GOOGLE_API_KEY

python -X utf8 -m ingest.inspect_parse   # sanity-check parsing
python -X utf8 -m ingest.build_index     # build the index (a few minutes)
```

Run the backend and frontend in separate terminals:

```bash
python -X utf8 -m uvicorn api.main:app --port 8000
cd frontend && npm install && npm run dev
```

Open http://localhost:5173.

## Demo

No demo recording is included in this repository. Producing one requires a live LLM API
key (Gemini/OpenAI) or a running Ollama instance to generate real grounded answers, which
wasn't available in the environment this project was built in. Recording a short screen
capture — asking a question, expanding a citation, asking a follow-up to show query
rewriting, and asking an out-of-scope question to show refusal — is a good first step for
anyone running this with a real API key.

## Switching providers

```bash
LLM_PROVIDER=gemini  LLM_MODEL=gemini-2.0-flash   # default, free tier
LLM_PROVIDER=openai  LLM_MODEL=gpt-4o-mini
LLM_PROVIDER=ollama  LLM_MODEL=llama3.1           # fully offline
```

Embeddings are always local, so switching providers never requires rebuilding the index.

## Tests

```bash
python -X utf8 -m pytest -v          # unit and API tests
python -X utf8 -m eval.run_eval      # retrieval evaluation
```

## What I'd do next

1. **Hybrid retrieval.** Add BM25 alongside vector search with reranking. Textbook
   queries are full of exact terms (`A* search`, `Bayesian network`) where embedding
   similarity alone underperforms.
2. **Prompt-technique comparison.** Add chain-of-thought and self-check answering, then
   compare all techniques on the eval set — the harness is already in place.
3. **Study modes.** Quiz generation, flashcards, chapter summarisation, and
   level-adjustable explanations as alternate prompt paths over the same retriever.

## Tech stack

Python 3.14 · LangChain · Chroma · sentence-transformers (`bge-small-en-v1.5`) ·
PyMuPDF · FastAPI · Pydantic v2 · React 18 · Vite · pytest
