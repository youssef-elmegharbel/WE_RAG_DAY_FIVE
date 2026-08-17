# Textbook RAG — Design Spec

**Date:** 2026-08-17
**Status:** Approved for planning

## 1. Purpose

A retrieval-augmented question-answering application over *Artificial Intelligence: A
Modern Approach* (4th ed., Russell & Norvig). A user asks a question in natural
language; the system answers using only content retrieved from the textbook, and cites
the chapter, section, and page it drew from.

The project serves two audiences at once:

- **Course deliverable.** Demonstrates each stage of the assigned pipeline —
  Textbook → RAG (LangChain) → prompt-engineering technique → LLM — as a distinct,
  inspectable component.
- **Portfolio piece.** Published as a public GitHub repository plus a recorded video
  demo shared on LinkedIn. There is no live deployment; the repository README and the
  video are the artifacts a reviewer will see.

Because the repository is public and the source textbook is copyrighted, the PDF and
any derived index are excluded from version control.

## 2. Scope

### In scope

- Multi-turn question answering grounded in the textbook, with per-answer citations.
- Structure-aware ingestion preserving chapter, section, and page metadata.
- Local embeddings, so the index is built once, offline, with no API key.
- Runtime-swappable generation provider: Gemini, OpenAI, or a local model via Ollama.
- Two prompt-engineering techniques: a grounded-answering prompt, and LLM query
  rewriting for follow-up questions.
- A ~20-question evaluation set with a script reporting retrieval hit-rate.
- React chat interface and FastAPI backend, run locally.

### Out of scope

- Public deployment or hosting of any kind.
- User accounts, authentication, or persistent server-side storage.
- Quiz generation, flashcards, and summarization modes (deferred — see expansion 3).
- Hybrid (BM25 + vector) retrieval and reranking.
- Frontend automated tests.

### Deferred expansions

These are explicitly planned successors, not vague possibilities. The design keeps the
door open for each without building it now.

1. **Hybrid retrieval.** Add BM25 keyword search alongside vector search with a
   reranking step. AI textbooks are dense with exact terms (`A* search`,
   `Bayesian network`) where pure embedding similarity underperforms.
2. **Prompt-technique comparison.** Add chain-of-thought and self-check answering, then
   evaluate all techniques against each other on the eval set. The evaluation harness
   built in this phase is the prerequisite.
3. **Additional study modes.** Quiz generation, flashcard generation, chapter
   summarization, and level-adjustable explanations (beginner through advanced), each
   implemented as an alternate prompt path over the same retriever. The chat interface
   gains a mode selector; retrieval, citations, and the provider layer are unchanged.

## 3. Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Application type | Grounded Q&A with citations | Clearest demo of the pipeline; other modes layer on later |
| Chunking | Structure-aware, within-section | Enables real citations ("Ch. 13.2, p. 412") and chapter filtering |
| Embeddings | Local `bge-small-en` | Free, offline, no key to build the index; index is provider-independent |
| Generation | Swappable; Gemini default | No API keys held yet; Gemini's free tier is usable without prepayment |
| Prompt technique | Grounded prompt + query rewriting | Grounding makes citations trustworthy; rewriting makes multi-turn work |
| Conversation state | Client-side, posted per request | No database needed for a local demo |
| Distribution | Repo + video; PDF gitignored | Avoids redistributing a copyrighted textbook |

**Note on embedding swappability.** Embeddings are deliberately *not* swappable. A
vector index is built with one embedding model and cannot be queried with another;
supporting multiple would mean maintaining one index per provider. Fixing embeddings
locally removes that burden entirely and makes offline operation genuinely true for the
retrieval half of the system.

## 4. Architecture

```
┌─────────────┐   HTTP    ┌──────────────┐
│  React SPA  │ ────────► │   FastAPI    │
│  (chat UI)  │ ◄──────── │              │
└─────────────┘  answer   └──────┬───────┘
                          + cites │
                    ┌─────────────┴─────────────┐
                    │      RAG Core (LangChain) │
                    │  rewrite → retrieve →     │
                    │  prompt → generate        │
                    └──────┬──────────────┬─────┘
                           │              │
                    ┌──────▼─────┐  ┌─────▼───────┐
                    │  Chroma    │  │ LLM Provider│
                    │  + local   │  │ Gemini /    │
                    │ embeddings │  │ OpenAI /    │
                    └────────────┘  │ Ollama      │
                                    └─────────────┘
```

### Boundaries

- The RAG core has no knowledge of HTTP. It is importable and testable on its own.
- FastAPI has no knowledge of LangChain internals. It calls one chain function and maps
  exceptions to status codes.
- All provider-specific detail lives in a single factory module. Swapping providers is
  one configuration value and touches no other file.

### Ingest flow (offline, run once)

```
PDF → structure-aware parse → within-section chunking
    → local embedding → persisted Chroma index at data/index/
```

### Query flow (per request)

```
question + history → rewrite to standalone query → vector search (top-k)
    → grounded prompt with context → LLM → {answer, citations, rewritten_query}
```

## 5. Components

### `ingest/` — offline, run once

- **`parse.py`** — PDF to structured text. Detects chapter and section headings, tracks
  page numbers, discards front and back matter. *This is the highest-risk component in
  the project;* extracting clean text from ~1100 pages of heavy mathematical typesetting
  is the most likely schedule overrun. It gets dedicated iteration time and a manual
  visual spot-check of its output before anything downstream is built.
- **`chunk.py`** — Splits text into ~1000-character chunks with 200-character overlap,
  never crossing a section boundary. Every chunk carries
  `{chapter_num, chapter_title, section, page_start, page_end}`.
- **`build_index.py`** — Embeds chunks with the local model and persists Chroma to
  `data/index/`. CLI entry point.

### `rag/` — core, pure Python

- **`providers.py`** — `get_llm(provider)` returns a configured LangChain chat model for
  `gemini`, `openai`, or `ollama`. The only module aware of provider-specific detail.
- **`embeddings.py`** — Wraps the local sentence-transformers model. Imported by both
  ingest and query paths, guaranteeing the same model is used on both sides.
- **`retriever.py`** — Loads the Chroma index, performs top-k search, returns chunks with
  metadata, and applies the relevance threshold.
- **`rewrite.py`** — Turns history plus the current question into a standalone search
  query. Falls back to the raw question on any failure.
- **`prompts.py`** — The grounded-answering prompt with few-shot examples covering the
  citation format and the insufficient-context refusal.
- **`chain.py`** — Wires rewrite → retrieve → prompt → generate. Returns
  `{answer, citations, rewritten_query}`.

### `api/` — FastAPI

- **`main.py`** — Application setup, CORS for local development, `GET /health`.
- **`routes.py`** — `POST /chat` accepting `{message, history}` and returning
  `{answer, citations, rewritten_query}`; `GET /config` reporting the active provider and
  model for display in the UI.
- **`schemas.py`** — Pydantic request and response models.

### `frontend/` — React + Vite

Chat view with message list and input. Each answer displays citation chips
("Ch. 13.2, p. 412") that expand to reveal the retrieved snippet — the feature that makes
the demo video persuasive, since it shows grounding rather than asserting it. Also
displays the active provider, loading state, and errors.

### `eval/`

- **`questions.yaml`** — ~20 questions paired with expected source chapters, hand-written
  against the textbook's actual content. Includes 2–3 questions deliberately outside the
  book's scope to verify the refusal path.
- **`run_eval.py`** — Reports retrieval hit-rate @k and dumps every answer with its
  citations for manual review.

### Deliberate omissions

No database — conversation history lives in the React client and is posted with each
request. No authentication. Both are unnecessary for a locally run demo.

## 6. Error Handling

The failures that matter here are retrieval failures, not crashes.

- **No relevant chunks.** If the top result falls below the similarity threshold, skip the
  LLM call entirely and return "That doesn't appear to be covered in the textbook."
  Cheaper and more honest than letting the model improvise.
- **Thin or off-topic context.** Handled in the prompt rather than in code: the few-shot
  examples demonstrate refusing when context is insufficient. This is the primary defense
  against hallucination, and the eval set is what confirms it works.
- **Query rewrite failure.** Fall back to the raw question and continue. Rewriting is an
  optimization and must never be a single point of failure.
- **Provider errors.** Rate limiting (most likely on Gemini's free tier), authentication
  failure, and timeouts each map to a distinct, actionable message. "Rate limited, wait a
  moment" helps the user; "500 Internal Server Error" does not.
- **Missing index at startup.** Fail loudly with a message pointing at `build_index.py`.
  A reviewer cloning the repository encounters this first, so it should read as
  instructions rather than as a bug.
- **Ingest failures.** Unparseable PDF, no chapters detected, or zero chunks produced all
  hard-fail with specifics. A silently half-ingested index is the worst possible outcome,
  because everything downstream appears to work while quietly returning garbage.

**Frontend.** Errors render as a message within the chat stream rather than as a modal,
and history is preserved so the user can retry without losing context.

## 7. Testing & Validation

### Unit tests (pytest; fast, no API calls, no model load)

- `chunk.py` — chunks never cross section boundaries; metadata complete on every chunk;
  overlap behaves correctly at section edges.
- `parse.py` — heading detection against fixture pages saved from the real PDF. The most
  likely site of regressions.
- `rewrite.py` — falls back to the raw question when the LLM call raises.
- `retriever.py` — below-threshold results trigger the no-answer path. Mocked embeddings.
- `providers.py` — each provider name yields the correct model class; an unknown name
  raises a clear error.

### Integration tests

Built against a small fixture index derived from roughly 20 real pages, committed as a
test fixture (a short excerpt, not the full text).

- End-to-end chain with a stubbed LLM: real retrieval and real prompt assembly, fake
  generation. Asserts that citations are populated and correspond to retrieved chunks.
- FastAPI routes via `TestClient` — request and response shapes, error mapping.

### Evaluation (manual, requires an API key)

`eval/run_eval.py` reports retrieval hit-rate @k — whether the expected chapter appears
in the top-k results — and dumps answers with citations for manual review. Run once per
provider. The resulting numbers go in the README and become the baseline for the
prompt-technique comparison in expansion 2.

### Frontend

No automated test suite. At this size, manual verification plus the demo video is the
honest cost/benefit trade; that time is better spent on the PDF parser.

## 8. Success Criteria

1. `build_index.py` ingests the full textbook and reports a plausible chapter and chunk
   count, verified by spot-checking parser output.
2. Asking a question covered by the textbook returns an accurate answer whose citations
   point at the correct chapter, confirmed by opening the book.
3. Asking a follow-up question ("explain that further") retrieves relevant chunks,
   demonstrating that query rewriting works.
4. Asking something outside the textbook produces a refusal rather than an invented
   answer.
5. Switching provider via configuration changes the answering model with no code edits.
6. `run_eval.py` produces a retrieval hit-rate figure suitable for the README.
7. The README documents architecture, setup, evaluation results, and the deferred
   expansions; the demo video shows the full flow including citation expansion.

## 9. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| PDF parsing quality | High — corrupts everything downstream | Build and spot-check the parser first, before any dependent component |
| Gemini free-tier rate limits | Medium — interrupts the demo | Map to a clear error; keep Ollama configured as an offline fallback |
| Local embedding model load time | Low — slow startup | Load once at application startup, not per request |
| Eval questions too easy | Medium — flattering, meaningless numbers | Include genuinely hard and out-of-scope questions |
