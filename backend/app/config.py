import os
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_root_env = os.path.join(_repo_root, ".env")
_backend_env = os.path.join(_repo_root, "backend", ".env")


class Settings(BaseSettings):
    """
    All application configuration loaded from environment variables.
    Validated at startup — invalid values cause an immediate, descriptive failure.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", _root_env, _backend_env),
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_secret_key: str = "change-me"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # ── Database ─────────────────────────────────────────────────
    database_url: str

    # ── Redis ────────────────────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"

    # ── Auth (JWT) ───────────────────────────────────────────────
    jwt_secret: str
    jwt_access_expiry: int = 900       # seconds
    jwt_refresh_expiry: int = 604800   # seconds

    # ── Admin seed user ──────────────────────────────────────────
    admin_email: str = "admin@example.com"
    admin_password: str

    # ── AI / LLM — Groq (primary) ────────────────────────────────
    ai_provider: Literal["groq", "openai", "anthropic", "google", "local", "mock"] = "groq"
    groq_api_key: str = ""
    ai_model_stage1: str = "llama-3.1-8b-instant"
    ai_model_stage2: str = "llama-3.3-70b-versatile"

    # ── Embeddings — OpenAI ──────────────────────────────────────
    openai_api_key: str = ""
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"

    # ── Fallback providers ───────────────────────────────────────
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # ── Apify connector (Reddit scraping) ────────────────────────
    apify_api_token: str = ""
    apify_reddit_actor: str = "trudax/reddit-scraper"

    # ── YouTube Data API v3 connector ────────────────────────────
    youtube_api_key: str = ""

    # ── Legacy Reddit direct API (deprecated, Apify preferred) ───
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "PhotoDiscoveryEngine/1.0"

    # ── Ingestion ────────────────────────────────────────────────
    batch_size: int = 100
    max_records_per_run: int = 5000
    ingestion_rate_limit_rpm: int = 60

    # ── Clustering ───────────────────────────────────────────────
    clustering_algorithm: Literal["dbscan", "kmeans", "hdbscan"] = "dbscan"
    cluster_min_samples: int = 5
    cluster_epsilon: float = 0.3

    # ── Thresholds ───────────────────────────────────────────────
    relevance_threshold: float = 0.7
    confidence_threshold: float = 0.6
    emerging_problem_growth_threshold: float = 0.25
    dedup_similarity_threshold: float = 0.95

    # ── Retention ────────────────────────────────────────────────
    data_retention_days: int = 365

    @field_validator("relevance_threshold", "confidence_threshold", "dedup_similarity_threshold", mode="before")
    @classmethod
    def validate_float_0_1(cls, v: float) -> float:
        v = float(v)
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("batch_size", mode="before")
    @classmethod
    def validate_batch_size(cls, v: int) -> int:
        v = int(v)
        if v < 1 or v > 10000:
            raise ValueError(f"batch_size must be between 1 and 10000, got {v}")
        return v


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton. Fails fast on startup if config is invalid."""
    return Settings()
