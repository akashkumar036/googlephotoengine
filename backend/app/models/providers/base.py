from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel


class BaseModelProvider(ABC):
    """
    Abstract base class for all AI/LLM providers (OpenAI, Groq, Anthropic, Google, Mock).
    Enforces standardized interfaces for structured classification and vector embedding.
    """

    provider_name: str = "base"

    @abstractmethod
    async def classify(
        self,
        text: str,
        prompt: str,
        model: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Send text and prompt to model, returning parsed dictionary (matching schema if provided).
        """
        raise NotImplementedError

    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        """
        Generate embedding vectors (1536-dimensional) for a batch of texts.
        """
        raise NotImplementedError
