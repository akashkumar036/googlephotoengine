from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Type
from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings
from app.models.providers.base import BaseModelProvider
from app.models.utils import extract_json_from_response

settings = get_settings()


class OpenAIProvider(BaseModelProvider):
    """OpenAI API provider for chat completions and vector embeddings."""

    provider_name: str = "openai"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url
        self.client = AsyncOpenAI(api_key=self.api_key or "sk-dummy", base_url=self.base_url)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    async def classify(
        self,
        text: str,
        prompt: str,
        model: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        chosen_model = model or "gpt-4o-mini"
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text[:16000]},  # Edge Case 1.4: max token boundary
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        chosen_model = model or settings.embedding_model or "text-embedding-3-small"
        sanitized_texts = [t.replace("\n", " ").strip() or " " for t in texts]

        # Edge Case 6.1: Sub-batching into 50 texts max per API call
        sub_batch_size = 50
        all_embeddings: List[List[float]] = []

        for i in range(0, len(sanitized_texts), sub_batch_size):
            chunk = sanitized_texts[i : i + sub_batch_size]
            resp = await self.client.embeddings.create(input=chunk, model=chosen_model)
            for item in resp.data:
                vec = item.embedding
                # Edge Case 6.3: Zero vector validation
                norm = math.sqrt(sum(x * x for x in vec))
                if norm < 1e-6:
                    vec[0] = 1e-4  # ensure non-zero representation
                all_embeddings.append(vec)

        return all_embeddings
