from __future__ import annotations
import math
import pytest
from app.models.providers.base import BaseModelProvider
from app.models.providers.mock import MockProvider, _generate_mock_embedding
from app.models.router import ModelRouter, get_model_router
from app.models.schemas import DeepAnalysisOutput, RelevanceOutput
from app.models.utils import extract_json_from_response, parse_and_validate


class DummyProvider(BaseModelProvider):
    async def classify(self, text: str, prompt: str, model=None, schema=None, temperature=0.0):
        return await super().classify(text, prompt, model, schema, temperature)

    async def embed(self, texts, model=None):
        return await super().embed(texts, model)


@pytest.mark.asyncio
async def test_base_provider_raises_not_implemented():
    provider = DummyProvider()
    with pytest.raises(NotImplementedError):
        await provider.classify("text", "prompt")
    with pytest.raises(NotImplementedError):
        await provider.embed(["text"])


@pytest.mark.asyncio
async def test_mock_provider_stage1_classification():
    provider = MockProvider()
    # Relevant text
    rel_res = await provider.classify(
        text="I cannot find photos from my Christmas trip 2023, search returns nothing",
        prompt="Stage 1 relevance classification prompt",
        schema=RelevanceOutput,
    )
    assert rel_res["is_relevant"] is True
    assert 0.0 <= rel_res["relevance_score"] <= 1.0
    assert len(rel_res["reasoning"]) > 0

    # Irrelevant text
    irrel_res = await provider.classify(
        text="Looking for lawn mower repair near downtown",
        prompt="Stage 1 relevance classification prompt",
        schema=RelevanceOutput,
    )
    assert irrel_res["is_relevant"] is False
    assert irrel_res["relevance_score"] < 0.5


@pytest.mark.asyncio
async def test_mock_provider_stage2_deep_analysis():
    provider = MockProvider()
    res = await provider.classify(
        text="I am looking for a screenshot of a receipt from Paris yesterday with my mom, but OCR failed and the date is wrong!",
        prompt="Stage 2 deep UX analysis prompt",
        schema=DeepAnalysisOutput,
    )
    assert res["primary_intent"] == "find_screenshot"
    assert "temporal" in res["memory_types"]
    assert "spatial" in res["memory_types"]
    assert "social" in res["memory_types"]
    assert any(m in res["failure_modes"] for m in ["unknown_date", "ocr_failure"])
    assert 0.0 <= res["frustration_level"] <= 1.0
    assert 0.0 <= res["severity"] <= 1.0
    assert 0.0 <= res["confidence"] <= 1.0
    assert len(res["reasoning_summary"]) > 0
    assert len(res["reasoning_summary"]) <= 500


@pytest.mark.asyncio
async def test_mock_provider_embeddings():
    provider = MockProvider()
    texts = ["Find photo of red car", "Lost vacation memories from Japan"]
    vectors = await provider.embed(texts)

    assert len(vectors) == 2
    for vec in vectors:
        assert len(vec) == 1536
        norm = math.sqrt(sum(x * x for x in vec))
        assert abs(norm - 1.0) < 0.01  # Normalized to unit length


def test_model_router_selection(monkeypatch):
    router = ModelRouter()

    # Default or mock
    prov = router.get_provider("mock")
    assert prov.provider_name == "mock"

    from app.config import get_settings
    settings = get_settings()

    # With valid API key, returns OpenAIProvider
    monkeypatch.setattr(settings, "openai_api_key", "sk-proj-valid-api-key-12345678")
    openai_prov = router.get_provider("openai")
    assert openai_prov.provider_name == "openai"

    # With valid Groq key, returns GroqProvider
    monkeypatch.setattr(settings, "groq_api_key", "gsk_valid_api_key_12345678")
    groq_prov = router.get_provider("groq")
    assert groq_prov.provider_name == "groq"

    # Stage 1 and Stage 2 models
    assert router.get_stage1_model("groq") == "llama-3.1-8b-instant"
    assert router.get_stage2_model("groq") == "llama-3.3-70b-versatile"
    assert router.get_stage1_model("openai") == "gpt-4o-mini"
    assert router.get_stage2_model("openai") == "gpt-4o"
    assert router.get_stage1_model("anthropic") == "claude-3-haiku-20240307"
    assert router.get_stage2_model("anthropic") == "claude-3-5-sonnet-20241022"


def test_json_extractor_and_repair():
    # 1. Plain json
    data = extract_json_from_response('{"score": 0.9, "valid": true}')
    assert data["score"] == 0.9
    assert data["valid"] is True

    # 2. Markdown code fences
    fenced = 'Here is your response:\n```json\n{"score": 0.85, "reason": "found keyword"}\n```\nHope that helps!'
    data_fenced = extract_json_from_response(fenced)
    assert data_fenced["score"] == 0.85
    assert data_fenced["reason"] == "found keyword"

    # 3. Trailing commas
    trailing = '{"items": ["a", "b",], "val": 10,}'
    data_trailing = extract_json_from_response(trailing)
    assert data_trailing["val"] == 10
