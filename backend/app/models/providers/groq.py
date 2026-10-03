from __future__ import annotations
from typing import Any, Dict, List, Optional, Type
from groq import AsyncGroq
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings
from app.models.providers.base import BaseModelProvider
from app.models.providers.openai import OpenAIProvider
from app.models.utils import extract_json_from_response

settings = get_settings()


class GroqProvider(BaseModelProvider):
    """Groq API provider for ultra-fast LLaMA-based classification."""

    provider_name: str = "groq"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.groq_api_key
        self.client = AsyncGroq(api_key=self.api_key or "gsk_dummy")
        self._embedding_fallback = OpenAIProvider()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    async def classify(
        self,
        text: str,
        prompt: str,
        model: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        chosen_model = model or settings.ai_model_stage1 or "llama-3.1-8b-instant"
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text[:16000]},
        ]

        response = await self.client.chat.completions.create(
            model=chosen_model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        parsed = extract_json_from_response(content)

        if schema:
            validated = schema.model_validate(parsed)
            return validated.model_dump()
        return parsed

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        # Groq delegates embedding generation to OpenAI or configured embedding provider
        return await self._embedding_fallback.embed(texts, model=model)
