"""Request and response models for the chat API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class HistoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[HistoryTurn] = Field(default_factory=list)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value.strip()


class CitationModel(BaseModel):
    label: str
    chapter_num: int
    chapter_title: str
    section: str
    section_title: str
    page_start: int
    page_end: int
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationModel]
    rewritten_query: str


class ConfigResponse(BaseModel):
    provider: str
    model: str
    top_k: int
