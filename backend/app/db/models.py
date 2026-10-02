"""
SQLAlchemy ORM models — all 15 tables as per architecture.md §5 and migrations.
Alembic migrations match these models with String(36) UUIDs and pgvector Vector(1536).
"""
from __future__ import annotations

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


# ─── users ────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(String(20), nullable=False, default="viewer")  # admin | researcher | viewer
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    human_reviews = relationship("HumanReview", back_populates="reviewer")


# ─── sources ──────────────────────────────────────────────────────────────
class Source(Base):
    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(100), unique=True, nullable=False)
    connector_type = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    config = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversations = relationship("Conversation", back_populates="source")


# ─── conversations ────────────────────────────────────────────────────────
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=_uuid)
    source_id = Column(String(36), ForeignKey("sources.id"), nullable=True)
    external_id = Column(String(500), nullable=True)
    url = Column(Text, nullable=True)
    author_hash = Column(String(64), nullable=True)   # SHA-256 of author
    timestamp = Column(DateTime(timezone=True), nullable=True)
    title = Column(Text, nullable=True)
    text = Column(Text, nullable=False)
    cleaned_text = Column(Text, nullable=True)
    language = Column(String(10), nullable=True)
    engagement = Column(JSONB, default=dict)
    metadata_ = Column("metadata", JSONB, default=dict)
    dedup_status = Column(String(20), default="original")  # original | duplicate | possible_duplicate | cross_post
    dedup_hash = Column(String(64), nullable=True, index=True)
    is_cleaned = Column(Boolean, default=False)
    is_relevant = Column(Boolean, nullable=True)
    is_low_information = Column(Boolean, default=False)
    is_spam = Column(Boolean, default=False)
    is_demo = Column(Boolean, default=False)
    was_truncated = Column(Boolean, default=False)
    embedding = Column(Vector(1536), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    needs_reanalysis = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source = relationship("Source", back_populates="conversations")
    analysis = relationship("AIAnalysis", back_populates="conversation", uselist=False)
    cluster_memberships = relationship("ClusterMembership", back_populates="conversation")
    evidence = relationship("Evidence", back_populates="conversation")


# ─── ai_analyses ─────────────────────────────────────────────────────────
class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(String(36), primary_key=True, default=_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, unique=True)
    prompt_version = Column(String(100), nullable=True)
    relevance = Column(Float, nullable=True)
    primary_intent = Column(String(100), nullable=True)
    memory_types = Column(JSONB, default=list)
    retrieval_strategies = Column(JSONB, default=list)
    failure_modes = Column(JSONB, default=list)
    pain_points = Column(JSONB, default=list)
    user_goal = Column(Text, nullable=True)
    known_memory = Column(JSONB, default=dict)
    unknown_memory = Column(JSONB, default=dict)
    frustration_level = Column(Float, nullable=True)
    severity = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    reasoning_summary = Column(Text, nullable=True)
    model_provider = Column(String(50), nullable=True)
    model_name = Column(String(100), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="analysis")


# ─── clusters ────────────────────────────────────────────────────────────
class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(String(36), primary_key=True, default=_uuid)
    label = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    member_count = Column(Integer, default=0)
    centroid = Column(Vector(1536), nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    memberships = relationship("ClusterMembership", back_populates="cluster")


# ─── cluster_memberships ──────────────────────────────────────────────────
class ClusterMembership(Base):
    __tablename__ = "cluster_memberships"

    conversation_id = Column(String(36), ForeignKey("conversations.id"), primary_key=True)
    cluster_id = Column(String(36), ForeignKey("clusters.id"), primary_key=True)
    similarity_score = Column(Float, nullable=True)

    conversation = relationship("Conversation", back_populates="cluster_memberships")
    cluster = relationship("Cluster", back_populates="memberships")


# ─── problems ────────────────────────────────────────────────────────────
class Problem(Base):
    __tablename__ = "problems"

    id = Column(String(36), primary_key=True, default=_uuid)
    title = Column(Text, nullable=False)
    statement = Column(Text, nullable=True)
    taxonomy_categories = Column(JSONB, default=list)
    frequency = Column(Integer, default=0)
    source_count = Column(Integer, default=0)
    frustration_score = Column(Float, nullable=True)
    severity_score = Column(Float, nullable=True)
    growth_rate = Column(Float, nullable=True)
    cross_source_score = Column(Float, nullable=True)
    evidence_diversity_score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    is_emerging = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    is_orphaned = Column(Boolean, default=False)
    user_segments = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    evidence = relationship("Evidence", back_populates="problem")
    opportunities = relationship("Opportunity", back_populates="problem")
    trends = relationship("Trend", back_populates="problem")


# ─── evidence ─────────────────────────────────────────────────────────────
class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=_uuid)
    problem_id = Column(String(36), ForeignKey("problems.id"), nullable=False)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    excerpt = Column(Text, nullable=True)
    ai_interpretation = Column(Text, nullable=True)
    relevance_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    problem = relationship("Problem", back_populates="evidence")
    conversation = relationship("Conversation", back_populates="evidence")


# ─── opportunities ────────────────────────────────────────────────────────
class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(String(36), primary_key=True, default=_uuid)
    problem_id = Column(String(36), ForeignKey("problems.id"), nullable=False)
    observed_problem = Column(Text, nullable=True)
    underlying_need = Column(Text, nullable=True)
    opportunity_area = Column(Text, nullable=True)
    solution_hypothesis = Column(Text, nullable=True)   # always labeled as hypothesis
    confidence = Column(Float, nullable=True)
    is_validated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    problem = relationship("Problem", back_populates="opportunities")


# ─── trends ───────────────────────────────────────────────────────────────
class Trend(Base):
    __tablename__ = "trends"

    id = Column(String(36), primary_key=True, default=_uuid)
    problem_id = Column(String(36), ForeignKey("problems.id"), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    conversation_count = Column(Integer, default=0)
    growth_rate = Column(Float, nullable=True)
    sources = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    problem = relationship("Problem", back_populates="trends")


# ─── human_reviews ───────────────────────────────────────────────────────
class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(String(36), primary_key=True, default=_uuid)
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    target_type = Column(String(50), nullable=False)    # conversation | problem | cluster | taxonomy
    target_id = Column(String(36), nullable=False)
    action = Column(String(50), nullable=False)         # approve | correct | merge | split | invalidate | bookmark
    original_value = Column(JSONB, default=dict)
    corrected_value = Column(JSONB, default=dict)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reviewer = relationship("User", back_populates="human_reviews")


# ─── jobs ─────────────────────────────────────────────────────────────────
class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=_uuid)
    type = Column(String(100), nullable=False)
    status = Column(String(20), default="queued")  # queued | running | done | failed | partial_success | dead_lettered
    progress = Column(Float, default=0.0)
    payload = Column(JSONB, default=dict)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── prompt_versions ─────────────────────────────────────────────────────
class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(String(100), primary_key=True)           # e.g. 'photo-retrieval-v1.3'
    stage = Column(String(50), nullable=False)            # relevance | analysis
    prompt_text = Column(Text, nullable=False)
    model_provider = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── research_reports ────────────────────────────────────────────────────
class ResearchReport(Base):
    __tablename__ = "research_reports"

    id = Column(String(36), primary_key=True, default=_uuid)
    title = Column(Text, nullable=True)
    content = Column(JSONB, default=dict)
    format = Column(String(20), default="markdown")  # markdown | pdf | json | csv
    generated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── evaluation_benchmarks ───────────────────────────────────────────────
class EvaluationBenchmark(Base):
    __tablename__ = "evaluation_benchmarks"

    id = Column(String(36), primary_key=True, default=_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    ground_truth_intent = Column(String(100), nullable=True)
    ground_truth_failure_modes = Column(JSONB, default=list)
    ground_truth_relevance = Column(Boolean, nullable=True)
    labeled_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
