from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class RelevanceOutput(BaseModel):
    """Stage 1 Relevance classification output schema."""
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    is_relevant: bool = Field(..., description="True if conversation is about photo retrieval difficulties")
    reasoning: str = Field(..., description="Brief reasoning for relevance classification")

    @field_validator("relevance_score", mode="before")
    @classmethod
    def clamp_score(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.0

    @field_validator("is_relevant", mode="before")
    @classmethod
    def coerce_bool(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.lower() in ("true", "yes", "1", "relevant")
        return bool(v)


class DeepAnalysisOutput(BaseModel):
    """Stage 2 Deep UX research extraction schema."""
    primary_intent: str = Field(
        default="find_photo",
        description="Core intent (e.g. find_photo, find_screenshot, find_video, find_album, organize_library, cleanup_storage)"
    )
    secondary_intents: List[str] = Field(default_factory=list)
    memory_types: List[str] = Field(
        default_factory=list,
        description="Memory dimensions referenced (temporal, spatial, social, visual, event, text, emotional)"
    )
    retrieval_strategies: List[str] = Field(
        default_factory=list,
        description="Strategies attempted (scroll_timeline, keyword_search, filter_album, map_view, people_tagging)"
    )
    failure_modes: List[str] = Field(
        default_factory=list,
        description="Specific failures encountered (unknown_date, ocr_failure, poor_ranking, face_recognition_fail, location_missing, query_mismatch, metadata_stripped)"
    )
    pain_points: List[str] = Field(default_factory=list)
    user_goal: Optional[str] = None
    known_memory: Dict[str, Any] = Field(default_factory=dict, description="What the user remembers (e.g. 'summer vacation', 'red dress')")
    unknown_memory: Dict[str, Any] = Field(default_factory=dict, description="What the user cannot remember (e.g. 'exact date', 'year')")
    frustration_level: float = Field(default=0.5, ge=0.0, le=1.0)
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    reasoning_summary: str = Field(default="", description="Concise summary (max 500 characters)")
    is_resolved: bool = Field(default=False, description="Whether user eventually resolved their problem")

    @field_validator("frustration_level", "severity", "confidence", mode="before")
    @classmethod
    def clamp_floats(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.5

    @field_validator("reasoning_summary", mode="after")
    @classmethod
    def truncate_summary(cls, v: str) -> str:
        if v and len(v) > 500:
            return v[:497] + "..."
        return v or ""
