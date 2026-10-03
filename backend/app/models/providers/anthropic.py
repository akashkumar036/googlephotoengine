from __future__ import annotations
from typing import Any, Dict, List, Optional, Type
from anthropic import AsyncAnthropic
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings
from app.models.providers.base import BaseModelProvider
from app.models.providers.openai import OpenAIProvider
from app.models.utils import extract_json_from_response

settings = get_settings()


class AnthropicProvider(BaseModelProvider):
    """Anthropic Claude API provider."""

    provider_name: str = "anthropic"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.client = AsyncAnthropic(api_key=self.api_key or "sk-ant-dummy")
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
        chosen_model = model or "claude-3-5-sonnet-20241022"
        response = await self.client.messages.create(
            model=chosen_model,
            max_tokens=4096,
            system=prompt,
            messages=[{"role": "user", "content": f"Return JSON only:\n{text[:16000]}"}],
            temperature=temperature,
        )
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

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
        return await self._embedding_fallback.embed(texts, model=model)
