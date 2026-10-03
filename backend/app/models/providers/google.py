from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Optional, Type
import google.generativeai as genai
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings
from app.models.providers.base import BaseModelProvider
from app.models.providers.openai import OpenAIProvider
from app.models.utils import extract_json_from_response

settings = get_settings()


class GoogleProvider(BaseModelProvider):
    """Google Gemini API provider."""

    provider_name: str = "google"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.google_api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
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
        chosen_model = model or "gemini-1.5-flash"
        generative_model = genai.GenerativeModel(
            model_name=chosen_model,
            system_instruction=prompt,
            generation_config={"temperature": temperature, "response_mime_type": "application/json"},
        )

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: generative_model.generate_content(text[:16000]),
        )
        content = response.text or ""
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
        # If google embedding is desired, or delegate to OpenAI
        return await self._embedding_fallback.embed(texts, model=model)
