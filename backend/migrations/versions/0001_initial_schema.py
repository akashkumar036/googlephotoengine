"""
Initial schema — all 15 tables with pgvector HNSW index.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector.sqlalchemy

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgvector extension is enabled in env.py before migrations run

    # ── users ──────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="viewer"),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── sources ────────────────────────────────────────────────────
    op.create_table(
        "sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("connector_type", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("config", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── conversations ──────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("external_id", sa.String(500), nullable=True),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("author_hash", sa.String(64), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("cleaned_text", sa.Text, nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("engagement", postgresql.JSONB, server_default="{}"),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("dedup_status", sa.String(20), server_default="original"),
        sa.Column("dedup_hash", sa.String(64), nullable=True),
        sa.Column("is_cleaned", sa.Boolean, server_default="false"),
        sa.Column("is_relevant", sa.Boolean, nullable=True),
        sa.Column("is_low_information", sa.Boolean, server_default="false"),
        sa.Column("is_spam", sa.Boolean, server_default="false"),
        sa.Column("is_demo", sa.Boolean, server_default="false"),
        sa.Column("was_truncated", sa.Boolean, server_default="false"),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.Column("embedding_model", sa.String(100), nullable=True),
        sa.Column("needs_reanalysis", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_conversations_dedup_hash", "conversations", ["dedup_hash"])
    op.create_index("ix_conversations_source_id", "conversations", ["source_id"])
    op.create_index("ix_conversations_timestamp", "conversations", ["timestamp"])

    # HNSW vector index for approximate nearest-neighbor search
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_conversations_embedding_hnsw
        ON conversations
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # ── ai_analyses ────────────────────────────────────────────────
    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id"), nullable=False, unique=True),
        sa.Column("prompt_version", sa.String(100), nullable=True),
        sa.Column("relevance", sa.Float, nullable=True),
        sa.Column("primary_intent", sa.String(100), nullable=True),
        sa.Column("memory_types", postgresql.JSONB, server_default="[]"),
        sa.Column("retrieval_strategies", postgresql.JSONB, server_default="[]"),
        sa.Column("failure_modes", postgresql.JSONB, server_default="[]"),
        sa.Column("pain_points", postgresql.JSONB, server_default="[]"),
        sa.Column("user_goal", sa.Text, nullable=True),
        sa.Column("known_memory", postgresql.JSONB, server_default="{}"),
        sa.Column("unknown_memory", postgresql.JSONB, server_default="{}"),
        sa.Column("frustration_level", sa.Float, nullable=True),
        sa.Column("severity", sa.Float, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("reasoning_summary", sa.Text, nullable=True),
        sa.Column("model_provider", sa.String(50), nullable=True),
        sa.Column("model_name", sa.String(100), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── clusters ───────────────────────────────────────────────────
    op.create_table(
        "clusters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("label", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("member_count", sa.Integer, server_default="0"),
        sa.Column("centroid", pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.Column("is_archived", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── cluster_memberships ────────────────────────────────────────
    op.create_table(
        "cluster_memberships",
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id"), primary_key=True),
        sa.Column("cluster_id", sa.String(36), sa.ForeignKey("clusters.id"), primary_key=True),
        sa.Column("similarity_score", sa.Float, nullable=True),
    )

    # ── problems ───────────────────────────────────────────────────
    op.create_table(
        "problems",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("statement", sa.Text, nullable=True),
        sa.Column("taxonomy_categories", postgresql.JSONB, server_default="[]"),
        sa.Column("frequency", sa.Integer, server_default="0"),
        sa.Column("source_count", sa.Integer, server_default="0"),
        sa.Column("frustration_score", sa.Float, nullable=True),
        sa.Column("severity_score", sa.Float, nullable=True),
        sa.Column("growth_rate", sa.Float, nullable=True),
        sa.Column("cross_source_score", sa.Float, nullable=True),
        sa.Column("evidence_diversity_score", sa.Float, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("is_emerging", sa.Boolean, server_default="false"),
        sa.Column("is_approved", sa.Boolean, server_default="false"),
        sa.Column("is_orphaned", sa.Boolean, server_default="false"),
        sa.Column("user_segments", postgresql.JSONB, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── evidence ───────────────────────────────────────────────────
    op.create_table(
        "evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("problem_id", sa.String(36), sa.ForeignKey("problems.id"), nullable=False),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("excerpt", sa.Text, nullable=True),
        sa.Column("ai_interpretation", sa.Text, nullable=True),
        sa.Column("relevance_score", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── opportunities ──────────────────────────────────────────────
    op.create_table(
        "opportunities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("problem_id", sa.String(36), sa.ForeignKey("problems.id"), nullable=False),
        sa.Column("observed_problem", sa.Text, nullable=True),
        sa.Column("underlying_need", sa.Text, nullable=True),
        sa.Column("opportunity_area", sa.Text, nullable=True),
        sa.Column("solution_hypothesis", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("is_validated", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── trends ─────────────────────────────────────────────────────
    op.create_table(
        "trends",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("problem_id", sa.String(36), sa.ForeignKey("problems.id"), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("conversation_count", sa.Integer, server_default="0"),
        sa.Column("growth_rate", sa.Float, nullable=True),
        sa.Column("sources", postgresql.JSONB, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── human_reviews ──────────────────────────────────────────────
    op.create_table(
        "human_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("reviewer_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("original_value", postgresql.JSONB, server_default="{}"),
        sa.Column("corrected_value", postgresql.JSONB, server_default="{}"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── jobs ────────────────────────────────────────────────────────
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), server_default="queued"),
        sa.Column("progress", sa.Float, server_default="0.0"),
        sa.Column("payload", postgresql.JSONB, server_default="{}"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── prompt_versions ────────────────────────────────────────────
    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("stage", sa.String(50), nullable=False),
        sa.Column("prompt_text", sa.Text, nullable=False),
        sa.Column("model_provider", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── research_reports ───────────────────────────────────────────
    op.create_table(
        "research_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("content", postgresql.JSONB, server_default="{}"),
        sa.Column("format", sa.String(20), server_default="markdown"),
        sa.Column("generated_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── evaluation_benchmarks ──────────────────────────────────────
    op.create_table(
        "evaluation_benchmarks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("ground_truth_intent", sa.String(100), nullable=True),
        sa.Column("ground_truth_failure_modes", postgresql.JSONB, server_default="[]"),
        sa.Column("ground_truth_relevance", sa.Boolean, nullable=True),
        sa.Column("labeled_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("evaluation_benchmarks")
    op.drop_table("research_reports")
    op.drop_table("prompt_versions")
    op.drop_table("jobs")
    op.drop_table("human_reviews")
    op.drop_table("trends")
    op.drop_table("opportunities")
    op.drop_table("evidence")
    op.drop_table("problems")
    op.drop_table("cluster_memberships")
    op.drop_table("clusters")
    op.drop_table("ai_analyses")
    op.drop_index("ix_conversations_embedding_hnsw", "conversations")
    op.drop_index("ix_conversations_timestamp", "conversations")
    op.drop_index("ix_conversations_source_id", "conversations")
    op.drop_index("ix_conversations_dedup_hash", "conversations")
    op.drop_table("conversations")
    op.drop_table("sources")
    op.drop_index("ix_users_email", "users")
    op.drop_table("users")
