from __future__ import annotations
import logging
from typing import Dict, Optional
from app.config import get_settings
from app.models.providers.anthropic import AnthropicProvider
from app.models.providers.base import BaseModelProvider
from app.models.providers.google import GoogleProvider
from app.models.providers.groq import GroqProvider
from app.models.providers.mock import MockProvider
from app.models.providers.openai import OpenAIProvider

logger = logging.getLogger(__name__)


def _is_valid_key(key: Optional[str]) -> bool:
    if not key:
        return False
    k = key.strip()
    if not k or "YOUR_" in k or "change-me" in k or k.endswith("_HERE") or k in ("gsk_dummy", "sk-dummy", "sk-ant-dummy"):
        return False
    return True


class ModelRouter:
    """
    Router that selects and provides the appropriate AI model provider
    based on application configuration, environment, and Stage 1 / Stage 2 requirements.
    """

    def __init__(self):
        self._providers: Dict[str, BaseModelProvider] = {}

    def get_provider(self, provider_name: Optional[str] = None) -> BaseModelProvider:
        settings = get_settings()
        name = (provider_name or settings.ai_provider or "groq").lower()

        if name not in self._providers:
            if name == "mock" or name == "local":
                self._providers[name] = MockProvider()
            elif name == "openai":
                if not _is_valid_key(settings.openai_api_key):
                    logger.info("Valid OPENAI_API_KEY not configured. Falling back to MockProvider.")
                    return MockProvider()
                self._providers[name] = OpenAIProvider()
            elif name == "groq":
                if not _is_valid_key(settings.groq_api_key):
                    logger.info("Valid GROQ_API_KEY not configured. Falling back to MockProvider.")
                    return MockProvider()
                self._providers[name] = GroqProvider()
            elif name == "anthropic":
                if not _is_valid_key(settings.anthropic_api_key):
                    logger.info("Valid ANTHROPIC_API_KEY not configured. Falling back to MockProvider.")
                    return MockProvider()
                self._providers[name] = AnthropicProvider()
            elif name == "google":
                if not _is_valid_key(settings.google_api_key):
                    logger.info("Valid GOOGLE_API_KEY not configured. Falling back to MockProvider.")
                    return MockProvider()
                self._providers[name] = GoogleProvider()
            else:
                logger.info("Unknown provider %s. Falling back to MockProvider.", name)
                self._providers[name] = MockProvider()

        return self._providers[name]

    def get_stage1_model(self, provider_name: Optional[str] = None) -> str:
        settings = get_settings()
        p = provider_name or settings.ai_provider
        if p == "groq":
            return settings.ai_model_stage1 or "llama-3.1-8b-instant"
        elif p == "openai":
            return "gpt-4o-mini"
        elif p == "anthropic":
            return "claude-3-haiku-20240307"
        elif p == "google":
            return "gemini-1.5-flash"
        return "mock-stage1"

    def get_stage2_model(self, provider_name: Optional[str] = None) -> str:
        settings = get_settings()
        p = provider_name or settings.ai_provider
        if p == "groq":
            return settings.ai_model_stage2 or "llama-3.3-70b-versatile"
        elif p == "openai":
            return "gpt-4o"
        elif p == "anthropic":
            return "claude-3-5-sonnet-20241022"
        elif p == "google":
            return "gemini-1.5-pro"
        return "mock-stage2"


_router = ModelRouter()


def get_model_router() -> ModelRouter:
    return _router
