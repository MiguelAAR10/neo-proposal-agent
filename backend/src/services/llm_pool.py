"""Singleton LLM instances — reuses HTTP connections across requests."""
from __future__ import annotations

from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import get_settings


@lru_cache(maxsize=1)
def get_chat_llm() -> ChatGoogleGenerativeAI:
    """Return cached LLM instance for chat/proposal generation."""
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_chat_model,
        temperature=0.3,
        google_api_key=settings.gemini_api_key,
    )


@lru_cache(maxsize=1)
def get_flash_llm() -> ChatGoogleGenerativeAI:
    """Return cached LLM instance for fast summarization tasks."""
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.2,
        google_api_key=settings.gemini_api_key,
    )
