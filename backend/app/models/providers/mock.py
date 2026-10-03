from __future__ import annotations
import hashlib
import math
import re
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel
from app.models.providers.base import BaseModelProvider
from app.models.schemas import DeepAnalysisOutput, RelevanceOutput


def _generate_mock_embedding(text: str, dim: int = 1536) -> List[float]:
    """Generate a deterministic, normalized vector of dimension `dim` based on text hash."""
    seed_hash = hashlib.sha256(text.encode("utf-8")).digest()
    vec = []
    for i in range(dim):
        b = seed_hash[i % len(seed_hash)]
        # Mix with index to avoid flat vector
        val = math.sin((i + 1) * (b + 1) * 0.12345)
        vec.append(val)
    # Normalize to unit length
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [round(x / norm, 6) for x in vec]


class MockProvider(BaseModelProvider):
    """
    Deterministic mock provider for unit testing, offline development,
    and demo dataset verification without external API keys.
    """

    provider_name: str = "mock"

    async def classify(
        self,
        text: str,
        prompt: str,
        model: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        lower_text = (text or "").lower()
        lower_prompt = (prompt or "").lower()

        # Check if Stage 1 (relevance) or Stage 2 (deep analysis)
        is_stage1 = "relevance" in lower_prompt or (schema and schema == RelevanceOutput)

        if is_stage1:
            # Stage 1: Relevance classification
            keywords = ["photo", "picture", "image", "screenshot", "video", "search", "find", "lost", "camera", "album", "gallery"]
            negative_keywords = ["lawn", "car repair", "crypto", "bitcoin", "cooking recipe", "weather forecast"]

            matches = sum(1 for kw in keywords if kw in lower_text)
            neg_matches = sum(1 for kw in negative_keywords if kw in lower_text)

            is_rel = (matches > 0 and neg_matches == 0) or ("relevant" in lower_text and "not relevant" not in lower_text)
            score = 0.88 if is_rel else 0.15

            out = RelevanceOutput(
                relevance_score=score,
                is_relevant=is_rel,
                reasoning=f"Mock heuristic detected {matches} retrieval keywords and {neg_matches} negative keywords.",
            )
            return out.model_dump()

        if "taxonomy architect" in lower_prompt or "outlier user feedback" in lower_prompt:
            return {
                "category_name": "SD Card & Hardware Corruption",
                "description": "Users encountering partial media corruption and broken headers on external storage.",
            }

        # Stage 2: Deep Analysis
        # Detect memory types
        memory_types = []
        if any(w in lower_text for w in ["yesterday", "year", "date", "when", "ago", "christmas", "summer", "timeline", "time"]):
            memory_types.append("temporal")
        if any(w in lower_text for w in ["beach", "paris", "japan", "home", "location", "place", "where", "trip", "city", "map"]):
            memory_types.append("spatial")
        if any(w in lower_text for w in ["mom", "dad", "friend", "wife", "husband", "dog", "cat", "people", "faces", "who", "baby"]):
            memory_types.append("social")
        if any(w in lower_text for w in ["red", "car", "sunset", "food", "screenshot", "receipt", "document", "text"]):
            memory_types.append("visual")
        if not memory_types:
            memory_types = ["temporal", "visual"]

        # Detect failure modes
        failure_modes = []
        if any(w in lower_text for w in ["date", "wrong date", "time", "order", "chronological"]):
            failure_modes.append("unknown_date")
        if any(w in lower_text for w in ["search", "nothing", "no results", "can't find", "cant find", "zero results"]):
            failure_modes.append("poor_ranking")
        if any(w in lower_text for w in ["face", "people", "person", "tag", "untagged"]):
            failure_modes.append("face_recognition_fail")
        if any(w in lower_text for w in ["text", "ocr", "receipt", "number"]):
            failure_modes.append("ocr_failure")
        if any(w in lower_text for w in ["location", "gps", "map", "city"]):
            failure_modes.append("location_missing")
        if not failure_modes:
            failure_modes = ["query_mismatch"]

        # Detect primary intent
        intent = "find_photo"
        if "screenshot" in lower_text:
            intent = "find_screenshot"
        elif "video" in lower_text:
            intent = "find_video"
        elif "album" in lower_text or "organize" in lower_text:
            intent = "organize_photos"
        elif "delete" in lower_text or "storage" in lower_text or "space" in lower_text:
            intent = "cleanup_storage"

        frustration = 0.85 if any(w in lower_text for w in ["frustrated", "annoying", "hate", "terrible", "worst", "broken", "useless", "ridiculous"]) else 0.55
        severity = 0.8 if "lost" in lower_text or "deleted" in lower_text or "missing" in lower_text else 0.5

        out = DeepAnalysisOutput(
            primary_intent=intent,
            secondary_intents=["keyword_search"] if "search" in lower_text else [],
            memory_types=memory_types,
            retrieval_strategies=["scroll_timeline", "keyword_search"],
            failure_modes=failure_modes,
            pain_points=[f"Difficulty locating media using {m} context" for m in memory_types[:2]],
            user_goal=f"Retrieve desired photo/media efficiently without knowing exact metadata",
            known_memory={"visual_clue": "media description remembered by user"},
            unknown_memory={"exact_date": "user cannot recall precise timestamp"},
            frustration_level=frustration,
            severity=severity,
            confidence=0.88,
            reasoning_summary=f"User attempted retrieval with {', '.join(memory_types)} cues but encountered {', '.join(failure_modes)}.",
            is_resolved=any(w in lower_text for w in ["solved", "never mind", "found it", "update:"]),
        )
        return out.model_dump()

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        return [_generate_mock_embedding(t or "") for t in texts]
