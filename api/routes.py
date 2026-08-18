"""HTTP routes. Translates chain results and failures into HTTP responses."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from api.schemas import ChatRequest, ChatResponse, ConfigResponse
from rag.chain import answer_question
from rag.config import get_settings
from rag.providers import UnknownProviderError
from rag.retriever import IndexNotFoundError

logger = logging.getLogger(__name__)
router = APIRouter()

RATE_LIMIT_MARKERS = ("429", "quota", "rate limit", "resource exhausted")
AUTH_MARKERS = ("api key", "unauthorized", "401", "invalid_api_key", "permission denied")


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/config", response_model=ConfigResponse)
def config() -> ConfigResponse:
    settings = get_settings()
    return ConfigResponse(
        provider=settings.provider,
        model=settings.model,
        top_k=settings.top_k,
    )


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = answer_question(
            question=request.message,
            history=[turn.model_dump() for turn in request.history],
        )
    except IndexNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "The textbook index has not been built yet. "
                "Run: python -m ingest.build_index"
            ),
        ) from exc
    except UnknownProviderError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        message = str(exc).lower()
        if any(marker in message for marker in RATE_LIMIT_MARKERS):
            raise HTTPException(
                status_code=429,
                detail="The model provider rate limit was reached. Wait a moment and try again.",
            ) from exc
        if any(marker in message for marker in AUTH_MARKERS):
            raise HTTPException(
                status_code=401,
                detail="The provider rejected the API key. Check your .env configuration.",
            ) from exc
        logger.exception("Unexpected failure while answering a question.")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while answering. Check the server logs.",
        ) from exc

    return ChatResponse(
        answer=result.answer,
        citations=[citation.__dict__ for citation in result.citations],
        rewritten_query=result.rewritten_query,
    )
