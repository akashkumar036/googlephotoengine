# Architecture: AI-Powered Photo Retrieval Discovery Engine

> **Based on:** `docs/context.md`
> **Generated:** 2026-10-02

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture Diagram](#2-high-level-architecture-diagram)
3. [Layer Breakdown](#3-layer-breakdown)
   - [3.1 Frontend](#31-frontend)
   - [3.2 API Layer](#32-api-layer)
   - [3.3 Research Orchestration Layer](#33-research-orchestration-layer)
   - [3.4 Data Connectors](#34-data-connectors)
   - [3.5 AI Analysis Engine](#35-ai-analysis-engine)
   - [3.6 Search & Vector Layer](#36-search--vector-layer)
   - [3.7 Background Job Processing](#37-background-job-processing)
   - [3.8 Storage Layer](#38-storage-layer)
   - [3.9 Insight Store](#39-insight-store)
4. [Data Flow](#4-data-flow)
5. [Database Schema](#5-database-schema)
6. [AI Pipeline Design](#6-ai-pipeline-design)
7. [Connector Architecture](#7-connector-architecture)
8. [API Contract](#8-api-contract)
9. [Frontend Pages & Components](#9-frontend-pages--components)
10. [Security Architecture](#10-security-architecture)
11. [Observability & Monitoring](#11-observability--monitoring)
12. [Cost Management Strategy](#12-cost-management-strategy)
13. [Configuration System](#13-configuration-system)
14. [Technology Stack Summary](#14-technology-stack-summary)
15. [Deployment Architecture](#15-deployment-architecture)
16. [Directory Structure](#16-directory-structure)

---

## 1. System Overview

The **Photo Retrieval Discovery Engine** is a full-stack AI-powered research platform. It ingests publicly available user conversations, processes them through an AI analysis pipeline, clusters them semantically, and surfaces structured product insights via a modern research dashboard.

**Core design principles:**
- **Source-agnostic ingestion** — new connectors can be added without touching the analysis pipeline
- **Model-provider agnostic AI** — LLM and embedding providers are swappable via a model abstraction layer
- **Evidence-first** — every insight traces back to the original conversation source
- **Human-in-the-loop** — AI classifications are reviewable and correctable by researchers
- **Problems before solutions** — the system discovers user needs; it does not prescribe fixes
- **Dynamic taxonomy** — problem categories evolve with incoming evidence

---

## 2. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        PUBLIC DATA SOURCES                      │
│  Reddit  │  Google Play  │  App Store  │  YouTube  │  Forums    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA CONNECTORS LAYER                        │
│  /reddit  /google-play  /app-store  /youtube  /google-community │
│                  (source-specific adapters)                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │  Normalized Records
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RAW DATA STORAGE (PostgreSQL)                │
│          source · source_id · url · author · timestamp          │
│          title · text · language · engagement · metadata        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               RESEARCH ORCHESTRATION LAYER                      │
│  (Celery / BullMQ — async job scheduling & coordination)        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   CLEANING   │  │  AI ANALYSIS     │  │  SEARCH ENGINE   │  │
│  │  Pipeline    │  │  Engine          │  │  (Semantic)      │  │
│  │              │  │                  │  │                  │  │
│  │ • Dedup      │  │ • Relevance      │  │ • Embedding      │  │
│  │ • Spam rm    │  │ • Intent         │  │   index          │  │
│  │ • Normalize  │  │ • Memory dims    │  │ • Vector search  │  │
│  │ • Lang detect│  │ • Failure modes  │  │ • NL query       │  │
│  │ • PII detect │  │ • Pain points    │  │   interface      │  │
│  └──────────────┘  │ • Clustering     │  └──────────────────┘  │
│                    │ • Problem gen    │                         │
│                    │ • Opportunity    │                         │
│                    │ • Trend detect   │                         │
│                    └──────────────────┘                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┼─────────────┐
              ▼            ▼             ▼
      ┌──────────┐  ┌──────────┐  ┌──────────────┐
      │   LLM    │  │Vector DB │  │  PostgreSQL  │
      │ Provider │  │(pgvector)│  │  (Insight    │
      │ (OpenAI/ │  │          │  │   Store)     │
      │ Claude/  │  │          │  │              │
      │ Gemini)  │  │          │  │              │
      └──────────┘  └──────────┘  └──────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER (FastAPI / Express)           │
│  POST /ingest  GET /conversations  GET /problems  GET /clusters │
│  GET /trends   GET /evidence/:id   POST /reviews                │
│  POST /research/query              POST /reports                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js + React)                   │
│                                                                 │
│  Overview │ Problems │ Problem Detail │ Conversations           │
│  Trends   │ Explore (NL Assistant)   │ Human Review            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Layer Breakdown

### 3.1 Frontend

**Technology:** Next.js 14+ (App Router), React, TypeScript, Tailwind CSS

**Responsibilities:**
- Render the 6-page research dashboard
- Communicate with the API layer via REST / WebSocket
- Display AI-generated insights with full evidence traceability
- Provide natural-language search and AI research assistant UI
- Allow human-review interactions (approve, correct, merge, split)
- Export research briefs (Markdown, PDF, CSV, JSON)

**Key pages:**

| Page | Route | Purpose |
|---|---|---|
| Overview | `/` | Stats, top problems, emerging problems, memory dimensions |
| Problems | `/problems` | Searchable/filterable problem list |
| Problem Detail | `/problems/:id` | Full evidence + trends + opportunities |
| Conversations | `/conversations` | Raw conversations with AI annotations |
| Trends | `/trends` | Time-series visualizations |
| Explore | `/explore` | Natural-language AI research assistant |
| Human Review | `/review` | Classification review queue |
| Evaluation | `/evaluation` | Model performance metrics (internal) |

**Design principles:**
- Clean information hierarchy; evidence is the primary artifact
- Fast client-side filtering
- Insight → Evidence navigation in ≤ 2 clicks
- No API keys exposed in browser

---

### 3.2 API Layer

**Technology:** Python / FastAPI (preferred) or Node.js / Express + TypeScript

**Responsibilities:**
- Expose RESTful endpoints consumed by the frontend
- Handle authentication & authorization (JWT / session)
- Route requests to the Research Orchestration Layer
- Validate and sanitize inputs
- Rate-limit external-facing endpoints

**Authentication middleware:**
```
Request → JWT Validation → Role Check → Handler → Response
```

**Role-based access:**

| Role | Permissions |
|---|---|
| Admin | Full access; configure sources, models, taxonomy |
| Researcher | Read/write; review, annotate, export |
| Viewer | Read-only; browse dashboard, export briefs |

---

### 3.3 Research Orchestration Layer

**Technology:** Celery (Python) or BullMQ (Node.js)

This layer coordinates the multi-stage analysis pipeline as asynchronous jobs. Every data-processing operation runs in the background.

**Job types:**

| Job | Trigger | Description |
|---|---|---|
| `ingest_source` | Manual / scheduled | Pull data from a connector |
| `clean_batch` | After ingestion | Dedup, normalize, PII detection |
| `analyze_batch` | After cleaning | Relevance filter → LLM analysis |
| `embed_batch` | After analysis | Generate embeddings for relevant records |
| `cluster_batch` | After embedding | Semantic clustering |
| `discover_problems` | After clustering | Problem synthesis |
| `detect_trends` | Scheduled | Time-series trend analysis |
| `detect_emerging` | Scheduled | New/rapidly growing problem detection |
| `generate_report` | On demand | Research brief generation |

**Job status tracking:**
```json
{
  "job_id": "uuid",
  "type": "analyze_batch",
  "status": "running | queued | done | failed",
  "progress": 0.73,
  "started_at": "...",
  "completed_at": "...",
  "error": null
}
```

---

### 3.4 Data Connectors

Each connector is an independent module that adapts a source-specific API or scraping method into the **normalized record schema**.

**Connector interface (abstract):**

```python
class BaseConnector:
    source_name: str

    def fetch(self, query: str, since: datetime, limit: int) -> List[RawRecord]:
        """Fetch raw records from the source."""
        raise NotImplementedError

    def normalize(self, raw: RawRecord) -> NormalizedRecord:
        """Transform raw record to common schema."""
        raise NotImplementedError
```

**Connectors (MVP):**

| Connector | Method | Status |
|---|---|---|
| Reddit | Reddit API (PRAW / official API) | MVP |
| Google Play | google-play-scraper / official API | MVP |
| App Store | app-store-scraper / iTunes API | MVP |
| Google Photos Community | RSS / permitted scraping | MVP |
| YouTube | YouTube Data API v3 | Post-MVP |
| Public Forums | RSS / permitted API | Post-MVP |

**Normalized record schema:**
```json
{
  "source": "reddit",
  "source_id": "t3_abc123",
  "url": "https://reddit.com/r/googlephotos/...",
  "author": "anon-hash-id",
  "timestamp": "2024-03-15T10:22:00Z",
  "title": "Can't find a photo from my vacation",
  "text": "I remember it was near a waterfall...",
  "language": "en",
  "engagement": {
    "likes": 42,
    "comments": 7,
    "shares": 0
  },
  "metadata": {
    "subreddit": "googlephotos",
    "flair": null
  }
}
```

---

### 3.5 AI Analysis Engine

**Technology:** LLM abstraction layer (provider-swappable)

**Model abstraction interface:**
```python
class BaseModelProvider:
    def classify(self, text: str, prompt_version: str) -> AIAnalysis:
        raise NotImplementedError

    def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError
```

**Primary provider:** Groq (OpenAI-compatible API — `base_url=https://api.groq.com/openai/v1`)

**Fallback providers:** OpenAI, Anthropic (Claude), Google (Gemini), local/OSS models (Ollama)

**Two-stage cost-optimized pipeline:**

```
Stage 1: Relevance Filter
  Model: Groq llama-3.1-8b-instant  (~500 tokens/s, ultra-low latency)
  Input: normalized text
  Output: { relevance: float, skip: bool }

Stage 2: Deep Analysis (relevant records only)
  Model: Groq llama-3.3-70b-versatile  (high quality reasoning)
  Input: normalized text
  Output: full AIAnalysis JSON
```

**Full AIAnalysis schema:**
```json
{
  "conversation_id": "uuid",
  "prompt_version": "photo-retrieval-v1.3",
  "relevance": 0.94,
  "primary_intent": "find_specific_photo",
  "memory_type": ["event", "location", "social"],
  "retrieval_strategy": ["keyword_search", "manual_scrolling"],
  "failure_modes": ["unknown_date", "semantic_search_failure"],
  "pain_points": ["cannot remember exact date", "too many irrelevant results"],
  "user_goal": "Find a specific photo from a college trip",
  "known_memory": {
    "event": "college trip",
    "scene": "waterfall",
    "people": "friends"
  },
  "unknown_memory": {
    "date": true,
    "location_exact": true
  },
  "frustration_level": 0.82,
  "severity": 0.71,
  "confidence": 0.91,
  "reasoning_summary": "User describes a photo retrieval attempt using event and visual memory...",
  "model_provider": "groq",
  "model_name": "llama-3.3-70b-versatile",
  "processed_at": "2024-03-15T12:00:00Z"
}
```

**Prompt versioning:**
- All prompts are stored with version identifiers (e.g., `photo-retrieval-v1.3`)
- Every analysis record stores the `prompt_version` used
- Enables future reprocessing and A/B evaluation

---

### 3.6 Search & Vector Layer

**Technology:** PostgreSQL + pgvector (MVP); optionally Pinecone or Weaviate

**Responsibilities:**
- Store and index vector embeddings for all analyzed conversations
- Power semantic clustering
- Power the natural-language search interface
- Power the AI research assistant context retrieval (RAG)

**Embedding pipeline:**
```
Analyzed conversation text
        ↓
Embedding model (e.g., text-embedding-3-small)
        ↓
Float vector (1536 dims)
        ↓
pgvector storage
        ↓
Approximate nearest-neighbor index (HNSW)
```

**Semantic clustering algorithm:**
1. Generate embeddings for all relevant conversations
2. Run HNSW approximate nearest-neighbor search
3. Apply DBSCAN or k-means over embedding space
4. Label clusters with AI-generated problem titles
5. Store cluster membership per conversation

**Natural-language search (RAG flow):**
```
User query (NL text)
        ↓
Embed query
        ↓
Vector similarity search (top-k conversations)
        ↓
Retrieved context passages
        ↓
LLM synthesis with citations
        ↓
Structured answer + evidence links
```

---

### 3.7 Background Job Processing

**Technology:** Celery + Redis (Python) or BullMQ + Redis (Node.js)

**Design:**
- All ingestion and analysis jobs are enqueued asynchronously
- Jobs are retried with exponential backoff on failure
- Job status is persisted in PostgreSQL and queryable via API
- Rate limits per connector are enforced at the job level
- Long jobs emit progress events (Server-Sent Events or WebSocket to frontend)

**Queue topology:**

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│  ingest     │    │  analysis   │    │  insight     │
│  queue      │    │  queue      │    │  queue       │
│             │    │             │    │              │
│ connector   │ →  │ clean       │ →  │ cluster      │
│ jobs        │    │ analyze     │    │ problem_gen  │
│             │    │ embed       │    │ trend_detect │
└─────────────┘    └─────────────┘    └──────────────┘
```

---

### 3.8 Storage Layer

**Primary database:** PostgreSQL

**Responsibilities:**
- Store normalized conversation records
- Store AI analysis results
- Store cluster assignments
- Store discovered problems and opportunities
- Store evidence links
- Store trend data (time-series)
- Store human review corrections
- Store job status
- Store prompt versions
- Store evaluation benchmark data

**Secondary (optional):** Redis for job queuing and caching

---

### 3.9 Insight Store

A logical grouping within PostgreSQL containing:
- Discovered problems (with scores)
- Opportunities (linked to problems)
- Evidence chains (conversation → problem → insight)
- Trends (time-series aggregations)
- Human review decisions

This is the **primary output** of the system, consumed by the dashboard.

---

## 4. Data Flow

### Ingestion Flow

```
1. Researcher triggers ingestion (UI or scheduled cron)
2. API enqueues ingest_source job
3. Connector fetches records from source API
4. Records normalized to common schema
5. Deduplication check (exact hash + semantic similarity)
6. New records written to raw storage (PostgreSQL)
7. clean_batch job enqueued
8. Cleaning pipeline runs (spam removal, PII detection, normalization)
9. Cleaned records flagged for analysis
10. analyze_batch job enqueued
```

### Analysis Flow

```
1. Stage 1: Cheap model relevance filter
   → Irrelevant records marked, skipped from expensive processing
2. Stage 2: Deep LLM analysis on relevant records
   → AIAnalysis JSON generated and stored
3. Embeddings generated for all relevant records
4. Embeddings stored in pgvector
5. Clustering job runs → clusters updated
6. Problem discovery job runs → problems synthesized/updated
7. Trends recalculated
8. Dashboard updated via API
```

### Research Assistant Flow (RAG)

```
1. Researcher submits NL query
2. Query embedded
3. Top-k most similar conversations retrieved from vector DB
4. Retrieved excerpts + metadata assembled as context
5. LLM generates a grounded answer with evidence citations
6. Response includes: answer + evidence list + problems + confidence
7. Researcher can drill into any cited conversation
```

---

## 5. Database Schema

### Core Tables

```sql
-- Data sources
CREATE TABLE sources (
  id UUID PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,   -- 'reddit', 'google_play', etc.
  connector_type VARCHAR(100) NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  config JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Raw + normalized conversations
CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  source_id UUID REFERENCES sources(id),
  external_id VARCHAR(500),            -- source's own ID
  url TEXT,
  author_hash VARCHAR(64),             -- anonymized
  timestamp TIMESTAMPTZ,
  title TEXT,
  text TEXT NOT NULL,
  language VARCHAR(10),
  engagement JSONB,
  metadata JSONB,
  dedup_status VARCHAR(20),            -- 'original' | 'duplicate' | 'possible_duplicate' | 'cross_post'
  dedup_hash VARCHAR(64),
  is_cleaned BOOLEAN DEFAULT FALSE,
  is_relevant BOOLEAN,
  embedding VECTOR(1536),              -- pgvector
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI analysis results
CREATE TABLE ai_analyses (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id),
  prompt_version VARCHAR(100),
  relevance FLOAT,
  primary_intent VARCHAR(100),
  memory_types JSONB,                  -- array of memory dimension tags
  retrieval_strategies JSONB,
  failure_modes JSONB,
  pain_points JSONB,
  user_goal TEXT,
  known_memory JSONB,
  unknown_memory JSONB,
  frustration_level FLOAT,
  severity FLOAT,
  confidence FLOAT,
  reasoning_summary TEXT,
  model_provider VARCHAR(50),
  model_name VARCHAR(100),
  processed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Semantic clusters
CREATE TABLE clusters (
  id UUID PRIMARY KEY,
  label TEXT,                          -- AI-generated cluster title
  description TEXT,
  member_count INT,
  centroid VECTOR(1536),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE cluster_memberships (
  conversation_id UUID REFERENCES conversations(id),
  cluster_id UUID REFERENCES clusters(id),
  similarity_score FLOAT,
  PRIMARY KEY (conversation_id, cluster_id)
);

-- Discovered problems
CREATE TABLE problems (
  id UUID PRIMARY KEY,
  title TEXT NOT NULL,
  statement TEXT,
  taxonomy_categories JSONB,           -- array of category tags
  frequency INT,
  source_count INT,
  frustration_score FLOAT,
  severity_score FLOAT,
  growth_rate FLOAT,
  cross_source_score FLOAT,
  evidence_diversity_score FLOAT,
  confidence FLOAT,
  is_emerging BOOLEAN DEFAULT FALSE,
  is_approved BOOLEAN DEFAULT FALSE,   -- human must approve emerging problems
  user_segments JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Evidence linking problems to conversations
CREATE TABLE evidence (
  id UUID PRIMARY KEY,
  problem_id UUID REFERENCES problems(id),
  conversation_id UUID REFERENCES conversations(id),
  excerpt TEXT,
  ai_interpretation TEXT,
  relevance_score FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Opportunity hypotheses
CREATE TABLE opportunities (
  id UUID PRIMARY KEY,
  problem_id UUID REFERENCES problems(id),
  observed_problem TEXT,
  underlying_need TEXT,
  opportunity_area TEXT,
  solution_hypothesis TEXT,            -- explicitly labeled as hypothesis
  confidence FLOAT,
  is_validated BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Time-series trends
CREATE TABLE trends (
  id UUID PRIMARY KEY,
  problem_id UUID REFERENCES problems(id),
  period_start TIMESTAMPTZ,
  period_end TIMESTAMPTZ,
  conversation_count INT,
  growth_rate FLOAT,
  sources JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Human review
CREATE TABLE human_reviews (
  id UUID PRIMARY KEY,
  reviewer_id UUID REFERENCES users(id),
  target_type VARCHAR(50),             -- 'conversation' | 'problem' | 'cluster' | 'taxonomy'
  target_id UUID,
  action VARCHAR(50),                  -- 'approve' | 'correct' | 'merge' | 'split' | 'invalidate' | 'bookmark'
  original_value JSONB,
  corrected_value JSONB,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users (internal)
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  role VARCHAR(20) NOT NULL,           -- 'admin' | 'researcher' | 'viewer'
  hashed_password VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Job tracking
CREATE TABLE jobs (
  id UUID PRIMARY KEY,
  type VARCHAR(100),
  status VARCHAR(20),
  progress FLOAT,
  payload JSONB,
  error TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prompt versions
CREATE TABLE prompt_versions (
  id VARCHAR(100) PRIMARY KEY,         -- e.g., 'photo-retrieval-v1.3'
  stage VARCHAR(50),                   -- 'relevance' | 'analysis'
  prompt_text TEXT NOT NULL,
  model_provider VARCHAR(50),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Research reports
CREATE TABLE research_reports (
  id UUID PRIMARY KEY,
  title TEXT,
  content JSONB,                       -- structured brief content
  format VARCHAR(20),                  -- 'markdown' | 'pdf' | 'json' | 'csv'
  generated_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Evaluation benchmarks
CREATE TABLE evaluation_benchmarks (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id),
  ground_truth_intent VARCHAR(100),
  ground_truth_failure_modes JSONB,
  ground_truth_relevance BOOLEAN,
  labeled_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Key Relationships

```
conversations ──── ai_analyses         (1:1 per prompt version)
conversations ──── cluster_memberships (M:M via clusters)
conversations ──── evidence            (M:M via problems)
problems      ──── evidence            (1:M)
problems      ──── opportunities       (1:M)
problems      ──── trends              (1:M time-series)
human_reviews ──── (any entity)        (polymorphic)
```

---

## 6. AI Pipeline Design

### Stage 1 — Relevance Filtering

**Prompt objective:** Determine if a conversation is relevant to photo/video retrieval problems.

**Input:** Raw conversation text (title + body)

**Output:**
```json
{
  "relevance_score": 0.94,
  "is_relevant": true,
  "reasoning": "User describes a specific failure to retrieve a photo..."
}
```

**Model:** Groq `llama-3.1-8b-instant` — ~500 tokens/s, sub-second latency, ideal for bulk filtering

**Fallback:** `gpt-3.5-turbo`, `gemini-1.5-flash`, `claude-haiku`

### Stage 2 — Deep Analysis

**Prompt objective:** Extract structured retrieval problem data from a relevant conversation.

**Input:** Cleaned conversation text

**Output:** Full `AIAnalysis` JSON (see §3.5)

**Model:** Groq `llama-3.3-70b-versatile` — high reasoning quality; OpenAI-compatible JSON mode

**Fallback:** `gpt-4o`, `claude-3-5-sonnet`, `gemini-1.5-pro`

### Stage 3 — Embedding

**Purpose:** Generate semantic vector representations for clustering and search.

**Model:** `text-embedding-3-small` (OpenAI) — Groq does not offer an embedding endpoint; OpenAI embeddings are used regardless of the LLM provider choice

### Stage 4 — Clustering

**Algorithm:**
1. Retrieve all embeddings
2. Run HNSW approximate nearest-neighbor (via pgvector)
3. Apply DBSCAN (density-based) or hierarchical clustering
4. For each cluster, generate a label using an LLM summary
5. Assign conversations to clusters with similarity scores

### Stage 5 — Problem Synthesis

**For each cluster (or group of related clusters):**
1. Sample representative conversations
2. Prompt LLM: "Synthesize the underlying recurring user problem"
3. Generate: title, statement, taxonomy categories, user segments
4. Calculate composite scores (frequency, severity, growth, evidence diversity)
5. Link supporting evidence

### Stage 6 — Trend Detection

**Time-series aggregation:**
- Group conversations by `timestamp` bucket (day/week/month)
- Count problem-tagged conversations per bucket
- Calculate growth rate vs. prior period
- Flag problems with sustained upward trend as "emerging"

### Stage 7 — Emerging Problem Detection

Detect problems that are:
- First appearing in the dataset (< 30 days old)
- Growing > X% week-over-week
- Appearing across ≥ 2 sources
- Not well-represented in the current taxonomy

Output a "Potential New Problem" record requiring human approval.

### Unknown Unknowns Detection

Run periodic **unsupervised** discovery:
- Identify conversations with low cluster similarity (outliers)
- Group outliers via topic modeling (LDA or BERTopic)
- Surface patterns not matching any existing taxonomy category
- Prompt: "What recurring pattern exists in these outlier conversations?"

---

## 7. Connector Architecture

### Connector Interface

```python
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

class BaseConnector(ABC):
    source_name: str
    rate_limit_per_minute: int = 60

    @abstractmethod
    def fetch(
        self,
        query: str,
        since: datetime,
        limit: int = 100
    ) -> List[dict]:
        """Fetch raw records from the source."""

    @abstractmethod
    def normalize(self, raw: dict) -> dict:
        """Map source-specific fields to normalized schema."""

    def run(self, query: str, since: datetime, limit: int = 100) -> List[dict]:
        """Fetch and normalize records (orchestrated)."""
        raw_records = self.fetch(query, since, limit)
        return [self.normalize(r) for r in raw_records]
```

### Reddit Connector

- **Method:** PRAW (Python Reddit API Wrapper) or official Reddit API
- **Data:** Posts and comments from relevant subreddits
  - `r/googlephotos`, `r/iphone`, `r/androidquestions`, `r/techsupport`, etc.
- **Search terms:** "find photo", "lost photo", "photo retrieval", "can't find memory", etc.
- **Compliance:** OAuth2 authentication, respect rate limits, no auth bypass

### Google Play Connector

- **Method:** `google-play-scraper` library or official API
- **Targets:** Google Photos, Apple Photos (cross-platform reviews), related apps
- **Fields:** rating, review text, date, version, thumbs-up count

### App Store Connector

- **Method:** iTunes Search API or `app-store-scraper`
- **Targets:** Google Photos iOS app, Apple Photos, other memory/photo apps
- **Fields:** rating, review text, date, helpful votes

### Google Photos Community Connector

- **Method:** RSS feed or permitted web access
- **Targets:** Google Photos Help Community public threads
- **Fields:** thread title, post body, replies, date

### Mock / Demo Connector

For sources that cannot be accessed:

```python
class MockConnector(BaseConnector):
    source_name = "demo"

    def fetch(self, query, since, limit):
        return load_demo_dataset()  # returns labeled DEMO DATA

    def normalize(self, raw):
        return {**raw, "source": "demo", "is_demo": True}
```

All mock data is clearly labeled `is_demo: true` and displayed as **DEMO DATA** in the UI.

---

## 8. API Contract

### Authentication

All endpoints require `Authorization: Bearer <JWT>` except `POST /auth/login`.

### Endpoints

#### Ingestion

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ingest` | Trigger data ingestion for a source |
| `GET` | `/jobs/:id` | Get job status |
| `GET` | `/jobs` | List all jobs with status |

**POST /ingest request:**
```json
{
  "source": "reddit",
  "query": "can't find photo",
  "since": "2024-01-01T00:00:00Z",
  "limit": 500
}
```

#### Conversations

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/conversations` | List conversations (paginated, filterable) |
| `GET` | `/conversations/:id` | Get single conversation with AI analysis |

**Filter params:** `source`, `language`, `intent`, `memory_type`, `failure_mode`, `from_date`, `to_date`, `cluster_id`, `problem_id`, `is_relevant`, `confidence_min`

#### Problems

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/problems` | List discovered problems (filterable) |
| `GET` | `/problems/:id` | Get problem detail with evidence + trends |
| `PATCH` | `/problems/:id` | Update problem (researcher annotation) |

#### Clusters

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/clusters` | List clusters |
| `GET` | `/clusters/:id` | Cluster detail with member conversations |

#### Trends

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/trends` | Get trend data (period + granularity params) |
| `GET` | `/trends/emerging` | Get emerging problem alerts |

#### Evidence

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/evidence/:id` | Get evidence record with source conversation |

#### Human Review

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/reviews/queue` | Get pending review items |
| `POST` | `/reviews` | Submit a review decision |

**POST /reviews request:**
```json
{
  "target_type": "conversation",
  "target_id": "uuid",
  "action": "correct",
  "corrected_value": {
    "primary_intent": "find_screenshot",
    "failure_modes": ["ocr_failure"]
  },
  "notes": "Reclassified: user was searching for a screenshot, not a photo"
}
```

#### Research

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/research/query` | Natural-language research query (RAG) |
| `POST` | `/reports` | Generate a research brief |
| `GET` | `/reports/:id` | Get a generated report |

**POST /research/query request:**
```json
{
  "query": "Why do users struggle to find photos when they don't remember the date?"
}
```

**POST /research/query response:**
```json
{
  "answer": "Based on 1,248 analyzed conversations...",
  "evidence": [
    {
      "conversation_id": "uuid",
      "source": "reddit",
      "url": "https://...",
      "excerpt": "I remember it was near a waterfall...",
      "intent": "find_specific_photo",
      "memory_type": ["event", "location"]
    }
  ],
  "problems": [
    { "id": "uuid", "title": "Unknown date retrieval failure" }
  ],
  "confidence": 0.89,
  "answer_type": "evidence_grounded"
}
```

---

## 9. Frontend Pages & Components

### Component Architecture

```
/app
  /layout.tsx                   — Auth check, sidebar, nav
  /page.tsx                     — Overview (/)
  /problems/page.tsx            — Problem list
  /problems/[id]/page.tsx       — Problem detail
  /conversations/page.tsx       — Conversation browser
  /trends/page.tsx              — Trend visualization
  /explore/page.tsx             — NL assistant
  /review/page.tsx              — Human review queue
  /evaluation/page.tsx          — Model eval (admin)

/components
  /ui/                          — Primitives (Button, Card, Badge, etc.)
  /charts/                      — Recharts/D3 time-series, heatmaps
  /evidence/
    EvidenceCard.tsx            — Single evidence display
    EvidenceViewer.tsx          — Expandable evidence panel
  /problems/
    ProblemCard.tsx
    ProblemFilters.tsx
    ProblemScoreBar.tsx         — Multi-dimension scoring viz
  /conversations/
    ConversationCard.tsx
    AnnotationOverlay.tsx
  /assistant/
    ResearchAssistant.tsx       — Chat-style NL query interface
    AnswerWithCitations.tsx
  /review/
    ReviewQueue.tsx
    ReviewCard.tsx
  /taxonomy/
    TaxonomyEditor.tsx
```

### Overview Page — Key Widgets

| Widget | Description |
|---|---|
| Stats bar | Total conversations, relevant %, sources, problems, emerging count |
| Top problems | Ranked table: problem + frequency + growth + source count |
| Emerging alerts | Problems with > X% growth in last 30 days |
| Memory dimension radar | Radar chart: date/location/people/events/objects/text/emotion |
| Failure mode breakdown | Bar chart of failure mode frequency |
| Source distribution | Pie/donut: Reddit, Play Store, App Store, etc. |
| Recent activity | Feed of newly discovered problems and trends |

---

## 10. Security Architecture

### Authentication

- JWT-based authentication (access token + refresh token)
- Tokens stored in HttpOnly cookies (not localStorage)
- Token expiry: access token 15 min, refresh token 7 days

### Authorization

- Role-based access control middleware on every API route
- Admin > Researcher > Viewer (hierarchical permissions)

### API Security

- HTTPS enforced everywhere
- CORS configured to allow only trusted origins
- Input validation and sanitization on all endpoints
- Rate limiting on public-facing endpoints

### Secrets Management

- All API keys in environment variables (never in frontend code or version control)
- `.env` not committed to git (`.gitignore`)
- Example `.env.example` provided for setup

### Data Privacy

- Author identifiers are hashed (SHA-256) before storage
- No raw emails, profiles, or PII stored
- Configurable data retention period
- Data deletion endpoints for compliance

---

## 11. Observability & Monitoring

### Structured Logging

All services emit structured JSON logs:
```json
{
  "timestamp": "...",
  "level": "INFO",
  "service": "ai_analysis",
  "job_id": "uuid",
  "event": "analysis_complete",
  "records_processed": 500,
  "duration_ms": 12400,
  "model": "gpt-4o",
  "prompt_version": "photo-retrieval-v1.3"
}
```

### Metrics to Track

| Metric | Description |
|---|---|
| Records ingested / hour | Ingestion rate per source |
| Relevance hit rate | % of conversations marked relevant |
| AI processing latency | P50/P95 per analysis stage |
| Embedding throughput | Embeddings generated / minute |
| Clustering job duration | Time to re-cluster on new data |
| LLM token cost | Tokens used per job, cumulative |
| API error rate | 4xx/5xx per endpoint |
| Review queue depth | Pending human reviews |

### Job Dashboard (UI — Admin)

- List all jobs with status, duration, error count
- Retry failed jobs
- Cancel running jobs

---

## 12. Cost Management Strategy

### Deduplication Before LLM

- Exact dedup: hash-based before any LLM call
- Semantic dedup: embedding similarity check before Stage 2 analysis
- Prevents re-processing the same content

### Two-Stage Model Routing

```
All records → Stage 1 (cheap model) → Relevance filter
                      ↓
             Relevant only → Stage 2 (expensive model) → Deep analysis
```

Expected cost reduction: 60–80% vs. sending all records to the expensive model.

### Caching

- Cache AI analysis results per `(conversation_id, prompt_version)`
- Cache embeddings per `conversation_id`
- Cache research query results for identical queries (short TTL)

### Configurable Analysis Depth

```
"analysis_depth": "shallow" | "standard" | "deep"
```

- **Shallow:** Stage 1 only (relevance + basic intent)
- **Standard:** Stage 1 + Stage 2 (full analysis)
- **Deep:** Stage 1 + Stage 2 + additional memory extraction pass

### Embedding Reuse

- Embeddings generated once per conversation version
- Only regenerated if the conversation text changes

---

## 13. Configuration System

All runtime parameters configurable via environment variables or a config file (no code changes required):

```env
# AI Provider
AI_PROVIDER=openai                    # openai | anthropic | google | local
AI_MODEL_STAGE1=gpt-3.5-turbo
AI_MODEL_STAGE2=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
AI_ANALYSIS_DEPTH=standard

# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Vector Search
VECTOR_DB=pgvector                    # pgvector | pinecone | weaviate
VECTOR_SIMILARITY_THRESHOLD=0.82

# Ingestion
BATCH_SIZE=100
MAX_RECORDS_PER_RUN=5000
INGESTION_RATE_LIMIT_RPM=60

# Clustering
CLUSTERING_ALGORITHM=dbscan          # dbscan | kmeans | hdbscan
CLUSTER_MIN_SAMPLES=5
CLUSTER_EPSILON=0.3

# Thresholds
RELEVANCE_THRESHOLD=0.7
CONFIDENCE_THRESHOLD=0.6
EMERGING_PROBLEM_GROWTH_THRESHOLD=0.25
DEDUP_SIMILARITY_THRESHOLD=0.95

# Retention
DATA_RETENTION_DAYS=365

# Security
JWT_SECRET=...
JWT_ACCESS_EXPIRY=900
JWT_REFRESH_EXPIRY=604800
```

---

## 14. Technology Stack

---

### 14.1 Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│  FRONTEND                                                           │
│  Next.js 14 (App Router) · React 18 · TypeScript 5                 │
│  Tailwind CSS · Recharts · Radix UI · NextAuth.js                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ REST / JSON
┌──────────────────────────────▼──────────────────────────────────────┐
│  BACKEND API                                                        │
│  Python 3.11+ · FastAPI · Uvicorn · Pydantic v2                     │
│  SQLAlchemy 2.0 · Alembic · python-jose · passlib                   │
└─────────┬────────────────────┬────────────────────┬─────────────────┘
          │                    │                    │
┌─────────▼──────┐  ┌─────────▼──────┐  ┌─────────▼──────────────┐
│  TASK QUEUE    │  │   AI LAYER     │  │   SEARCH LAYER         │
│  Celery 5      │  │  Groq SDK      │  │  pgvector (PostgreSQL)  │
│  Redis 7       │  │  (OAI-compat.) │  │  SQLAlchemy ANN queries │
│  Celery Beat   │  │  + OpenAI Emb. │  │                         │
└─────────┬──────┘  └─────────┬──────┘  └─────────────────────────┘
          │                    │
┌─────────▼────────────────────▼──────────────────────────────────────┐
│  DATA LAYER                                                         │
│  PostgreSQL 16 + pgvector extension                                 │
│  Redis 7 (job broker + cache)                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 14.2 Frontend

| Technology | Version | Purpose | Rationale |
|---|---|---|---|
| **Next.js** | 14+ (App Router) | React framework, SSR, routing | App Router enables server components for fast initial load; built-in API routes if needed |
| **React** | 18+ | UI component model | Industry standard; concurrent rendering for smooth interactions |
| **TypeScript** | 5+ | Static typing | Catches interface mismatches between API and UI at compile time |
| **Tailwind CSS** | 3+ | Utility-first styling | Rapid design iteration; consistent design tokens across all components |
| **Recharts** | 2+ | Data visualization | Composable chart library; native React integration; supports time-series, radar, bar, donut |
| **Radix UI** | Latest | Accessible UI primitives | Headless, accessible components (Modal, Tabs, Tooltip, Dropdown) that can be styled freely |
| **Lucide React** | Latest | Icon set | Consistent, clean icon system |
| **NextAuth.js** | 4+ | Authentication | Handles JWT session management; credential provider connects to backend JWT |
| **Axios** | 1+ | HTTP client | Interceptors for automatic auth header injection and token refresh |
| **date-fns** | 3+ | Date utilities | Lightweight date formatting and manipulation for trend charts |

**Key frontend design decisions:**
- **App Router (not Pages Router):** Server components reduce client-side JavaScript for data-heavy pages
- **Tailwind over CSS Modules:** Design system enforced at utility level; no class naming conflicts
- **Recharts over Chart.js:** Better React integration; composable API for custom chart layouts
- **Radix UI over MUI/Chakra:** Zero styling opinions; full design control; WCAG accessibility built in

---

### 14.3 Backend API

| Technology | Version | Purpose | Rationale |
|---|---|---|---|
| **Python** | 3.11+ | Primary language | Strong ML/AI ecosystem; async support; best LLM SDK support |
| **FastAPI** | 0.110+ | REST API framework | Automatic OpenAPI docs; Pydantic-native validation; async-first |
| **Uvicorn** | 0.29+ | ASGI server | High-performance async server for FastAPI |
| **Pydantic** | v2 | Data validation & settings | Schema validation for all API inputs/outputs and AI response parsing |
| **SQLAlchemy** | 2.0+ | ORM | Async query support; declarative models; works with Alembic migrations |
| **Alembic** | Latest | DB migrations | Version-controlled schema changes; supports pgvector DDL |
| **python-jose** | Latest | JWT encoding/decoding | JWT issue and verification for auth |
| **passlib + bcrypt** | Latest | Password hashing | Secure credential storage |
| **httpx** | Latest | Async HTTP client | Used internally by connectors for async API calls |
| **structlog** | Latest | Structured logging | JSON log output with context binding per request/job |

**Key backend design decisions:**
- **FastAPI over Django REST / Flask:** Async-native; automatic schema generation; fastest Python API framework
- **SQLAlchemy 2.0:** Unified async + sync API; no need for separate async ORM
- **Pydantic v2:** 5–50× faster validation than v1; essential for parsing thousands of LLM JSON responses

---

### 14.4 AI & LLM Layer

> **Primary LLM Provider: Groq**
> Groq exposes an OpenAI-compatible REST API (`base_url=https://api.groq.com/openai/v1`).
> The existing `openai` Python SDK is used — only the `base_url` and `api_key` differ.
> No separate Groq SDK is required.

#### LLM Providers (model-abstraction layer — swappable)

| Priority | Provider | Stage 1 Model (Relevance) | Stage 2 Model (Deep Analysis) | SDK |
|---|---|---|---|---|
| ✅ **Primary** | **Groq** | `llama-3.1-8b-instant` | `llama-3.3-70b-versatile` | `openai` SDK + Groq `base_url` |
| Fallback | OpenAI | `gpt-3.5-turbo` | `gpt-4o` | `openai` Python SDK |
| Fallback | Anthropic | `claude-haiku-3` | `claude-3-5-sonnet` | `anthropic` Python SDK |
| Fallback | Google | `gemini-1.5-flash` | `gemini-1.5-pro` | `google-generativeai` SDK |
| Fallback | Local / OSS | `llama-3-8b` (via Ollama) | `llama-3-70b` (via Ollama) | `openai`-compatible API |

**Groq model characteristics:**

| Model | Role | Speed | Context | Strengths |
|---|---|---|---|---|
| `llama-3.1-8b-instant` | Stage 1 | ~500 tok/s | 128K tokens | Ultra-low latency; ideal for bulk relevance filtering |
| `llama-3.3-70b-versatile` | Stage 2 | ~100 tok/s | 128K tokens | Strong instruction following; reliable JSON mode |
| `mixtral-8x7b-32768` | Stage 2 (alt) | ~150 tok/s | 32K tokens | Strong multilingual; alternative to 70b |

**Integration — Groq via OpenAI SDK:**
```python
from openai import OpenAI

client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# Stage 1 — fast relevance filter
response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"}
)

# Stage 2 — deep analysis
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"}
)
```

**Provider routing in `.env`:**
```env
AI_PROVIDER=groq
GROQ_API_KEY=gsk_...
AI_MODEL_STAGE1=llama-3.1-8b-instant
AI_MODEL_STAGE2=llama-3.3-70b-versatile
```

#### Embedding Models

> **Note:** Groq does not offer an embedding endpoint.
> OpenAI embeddings are used regardless of the LLM provider setting.

| Provider | Model | Dimensions | Use Case |
|---|---|---|---|
| **OpenAI** (required) | `text-embedding-3-small` | 1536 | All conversation embeddings (default) |
| **OpenAI** (high-quality) | `text-embedding-3-large` | 3072 | Optional upgrade for better recall |
| **Local / OSS** | `nomic-embed-text` (via Ollama) | 768 | Air-gapped / zero-cost option |

```env
# Embeddings always use OpenAI regardless of AI_PROVIDER
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_PROVIDER=openai
```

**Rationale for two-stage LLM routing with Groq:**
```
Stage 1 — Groq llama-3.1-8b-instant:
  Cost:  ~$0.05 / 1M tokens  (extremely cheap)
  Speed: ~500 tokens/sec     (near-instant)
  Purpose: bulk relevance filter (60–80% of records skipped here)

Stage 2 — Groq llama-3.3-70b-versatile:
  Cost:  ~$0.59 / 1M tokens  (still much cheaper than GPT-4o)
  Speed: ~100 tokens/sec
  Purpose: full structured extraction (relevant records only)

Embeddings — OpenAI text-embedding-3-small:
  Cost:  ~$0.02 / 1M tokens
  Speed: batch API; ~100 texts/call

Net cost vs. GPT-4o on all records: ~90% reduction
```

#### Supporting AI Libraries

| Library | Purpose |
|---|---|
| `openai` | Primary SDK — used for both Groq (via `base_url`) and OpenAI embeddings |
| `tiktoken` | Token counting before API calls (prevent context overflow) |
| `tenacity` | Retry logic with exponential backoff for LLM/embedding API calls |
| `bertopic` or `sklearn` | Unsupervised topic modeling for unknown-unknowns detection |
| `presidio-analyzer` | PII detection in raw conversation text |
| `langdetect` or `lingua` | Language detection per record |

---

### 14.5 Data & Storage Layer

| Technology | Version | Purpose | Rationale |
|---|---|---|---|
| **PostgreSQL** | 16 | Primary relational database | Rock-solid; supports pgvector; JSONB for flexible metadata; ACID guarantees |
| **pgvector** | 0.7+ | Vector similarity search | Embedded in PostgreSQL; eliminates separate vector DB for MVP; HNSW index for ANN |
| **Redis** | 7+ | Job broker + result backend + cache | Celery broker; short-lived cache for LLM results; session tokens |

**pgvector HNSW index configuration:**
```sql
CREATE INDEX ON conversations
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
```

| Parameter | Value | Meaning |
|---|---|---|
| `m` | 16 | Max connections per node (higher = better recall, more memory) |
| `ef_construction` | 64 | Build-time search width (higher = better quality, slower build) |
| Distance function | `vector_cosine_ops` | Cosine similarity — best for normalized text embeddings |

**When to upgrade from pgvector to a dedicated vector DB:**

| Scale | Recommendation |
|---|---|
| < 500K records | pgvector (MVP) — fully sufficient |
| 500K – 5M records | Consider Weaviate or Qdrant |
| > 5M records | Pinecone or Weaviate with horizontal scaling |

---

### 14.6 Background Job Processing

| Technology | Version | Purpose | Rationale |
|---|---|---|---|
| **Celery** | 5+ | Distributed task queue | Mature Python ecosystem; supports retry, chaining, rate limiting |
| **Celery Beat** | (bundled) | Periodic job scheduler | Cron-like scheduling for trend detection, emerging problem detection |
| **Redis** (broker) | 7+ | Message broker for Celery | Fast in-memory; reliable; supports Celery's required data structures |
| **Flower** (optional) | Latest | Celery monitoring UI | Real-time task monitoring; admin visibility into queue depth and failures |

**Queue topology:**

| Queue | Workers | Tasks |
|---|---|---|
| `ingest` | 2 workers | Connector fetch jobs |
| `analysis` | 4 workers | Clean, relevance filter, deep analysis, embed |
| `insight` | 2 workers | Cluster, problem discovery, trend detection |
| `reports` | 1 worker | Research brief generation |

**Alternative: BullMQ (Node.js)**
If the backend is Node.js/TypeScript instead of Python:

| Technology | Purpose |
|---|---|
| **BullMQ** | Job queue (Redis-backed) |
| **Bull Board** | Queue monitoring UI |

---

### 14.7 Data Connector Libraries

| Connector | Library | Notes |
|---|---|---|
| Reddit | `praw` (Python Reddit API Wrapper) | Official Reddit OAuth2 API |
| Google Play | `google-play-scraper` | Unofficial scraper; use with rate limiting |
| App Store | `app-store-scraper` | iTunes RSS API + scraping |
| YouTube | `google-api-python-client` | YouTube Data API v3; requires API key |
| Google Community | `feedparser` or `httpx` | RSS feed or permitted scraping |
| Generic web | `httpx` + `beautifulsoup4` | For permitted forum/blog sources |

---

### 14.8 Data Processing & Cleaning Libraries

| Library | Purpose |
|---|---|
| `ftfy` | Fix Unicode encoding issues in text |
| `beautifulsoup4` | Safe HTML stripping |
| `langdetect` | Language detection per record |
| `presidio-analyzer` | PII detection (emails, phone numbers, names) |
| `hashlib` | SHA-256 hashing for dedup and author anonymization |
| `chardet` | Encoding detection for raw bytes |

---

### 14.9 Authentication & Security

| Technology | Purpose |
|---|---|
| `python-jose` | JWT encode/decode (access + refresh tokens) |
| `passlib[bcrypt]` | Secure password hashing |
| `python-multipart` | Form data parsing for login endpoint |
| `slowapi` | FastAPI rate limiting middleware |
| `detect-secrets` | Pre-commit hook to block secret commits |
| HTTPS (TLS) | Enforced on all deployed environments |

**JWT configuration:**

| Token | Expiry | Storage |
|---|---|---|
| Access token | 15 minutes | HttpOnly cookie |
| Refresh token | 7 days | HttpOnly cookie |

---

### 14.10 Testing

| Technology | Purpose |
|---|---|
| `pytest` | Python test runner |
| `pytest-asyncio` | Async test support (FastAPI routes, Celery tasks) |
| `httpx` (test client) | FastAPI `TestClient` for integration tests |
| `factory_boy` | Test fixture generation |
| `unittest.mock` | Mock LLM providers in unit tests |
| `pytest-cov` | Coverage reporting (target: 80% on critical paths) |
| `Playwright` or `Cypress` | Frontend E2E testing |
| `Jest` + `React Testing Library` | Frontend unit and component tests |

---

### 14.11 Observability

| Technology | Purpose |
|---|---|
| `structlog` | Structured JSON logging (backend) |
| `prometheus-client` | Metrics exposure (optional) |
| `Flower` | Celery queue monitoring |
| Sentry (optional) | Error tracking and alerting |
| Custom `/admin/metrics` API | In-app system health page |

---

### 14.12 DevOps & Infrastructure

| Technology | Version | Purpose |
|---|---|---|
| **Docker** | 24+ | Container packaging |
| **Docker Compose** | v2 | Local multi-service orchestration |
| **Dockerfile** (backend) | Python 3.11-slim base | Minimal image size |
| **Dockerfile** (frontend) | Node 20-alpine base | Lightweight Next.js image |
| **Alembic** | Latest | Database schema migrations |
| **GitHub Actions** (optional) | — | CI: lint, test, secret scan on every PR |

**Local dev requirements:**

| Requirement | Minimum Version |
|---|---|
| Docker Desktop | 4.x |
| Docker Compose | v2.x |
| Node.js (for frontend dev) | 20 LTS |
| Python (for backend dev) | 3.11+ |

---

### 14.13 Full Dependency Reference

#### Backend `requirements.txt`

```txt
# API Framework
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
python-multipart>=0.0.9

# Data Validation
pydantic>=2.6.0
pydantic-settings>=2.2.0

# Database
sqlalchemy>=2.0.0
alembic>=1.13.0
psycopg2-binary>=2.9.9
pgvector>=0.2.5

# Job Queue
celery>=5.3.6
redis>=5.0.3
flower>=2.0.1

# AI / LLM
# Groq is the primary provider — uses the openai SDK with a custom base_url
# The same openai SDK is also used for OpenAI embeddings
openai>=1.14.0          # used for Groq (base_url=https://api.groq.com/openai/v1) + OpenAI embeddings
tiktoken>=0.6.0
tenacity>=8.2.3
# Optional fallback providers (install only if switching provider)
# anthropic>=0.21.0
# google-generativeai>=0.5.0

# Embeddings / ML
scikit-learn>=1.4.0
numpy>=1.26.0

# Data Connectors
praw>=7.7.1
google-play-scraper>=1.2.4
app-store-scraper>=0.3.5
google-api-python-client>=2.119.0
httpx>=0.27.0
beautifulsoup4>=4.12.3
feedparser>=6.0.11

# Text Processing
ftfy>=6.2.0
langdetect>=1.0.9
presidio-analyzer>=2.2.352
chardet>=5.2.0

# Auth & Security
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
slowapi>=0.1.9

# Logging & Observability
structlog>=24.1.0

# Testing
pytest>=8.1.0
pytest-asyncio>=0.23.5
pytest-cov>=5.0.0
httpx>=0.27.0  # TestClient
factory-boy>=3.3.0
```

#### Frontend `package.json` (key dependencies)

```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "typescript": "^5.4.0",
    "axios": "^1.6.8",
    "next-auth": "^4.24.7",
    "recharts": "^2.12.3",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-tooltip": "^1.0.7",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "lucide-react": "^0.368.0",
    "date-fns": "^3.6.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.2.2"
  },
  "devDependencies": {
    "tailwindcss": "^3.4.3",
    "postcss": "^8.4.38",
    "autoprefixer": "^10.4.19",
    "@types/react": "^18.3.1",
    "@types/node": "^20.12.7",
    "jest": "^29.7.0",
    "@testing-library/react": "^15.0.6",
    "@testing-library/jest-dom": "^6.4.2",
    "eslint": "^8.57.0",
    "eslint-config-next": "^14.2.0"
  }
}
```

---

### 14.14 Alternatives Considered

| Layer | Chosen | Alternatives Considered | Why Chosen |
|---|---|---|---|
| Backend language | Python | Node.js/TypeScript | Python has better LLM/ML library ecosystem; native numpy for embeddings |
| API framework | FastAPI | Django REST, Flask, Express | FastAPI: fastest, async-native, auto OpenAPI docs |
| Vector DB | pgvector | Pinecone, Weaviate, Qdrant, Chroma | Avoids separate service for MVP; Postgres handles everything; migrate later if scale demands |
| Task queue | Celery | BullMQ, Temporal, n8n, Airflow | Celery: Python-native; simple setup; mature retry/chaining support |
| LLM provider | **Groq** (primary) | OpenAI, Anthropic, Google, Ollama | Groq offers the lowest latency inference (~500 tok/s on 8B models) at a fraction of OpenAI cost; OpenAI-compatible API means zero SDK changes; abstraction layer keeps other providers as fallbacks |
| Frontend framework | Next.js | Vite + React, Remix | Next.js: App Router SSR for data-heavy pages; largest ecosystem |
| CSS framework | Tailwind | CSS Modules, styled-components, MUI | Tailwind: no naming collisions; fastest iteration; no runtime overhead |
| Auth | JWT (custom) | Auth0, Clerk, Supabase Auth | Custom JWT: no external dependency; full control; simple for internal tool |
| Charts | Recharts | D3.js, Chart.js, Nivo | Recharts: React-native; composable; easier than raw D3 for standard chart types |

---

## 15. Deployment Architecture

### Local Development (Docker Compose)

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:
    build: ./backend
    depends_on: [db, redis]
    env_file: .env
    ports: ["8000:8000"]

  worker:
    build: ./backend
    command: celery -A app.worker worker
    depends_on: [db, redis]
    env_file: .env

  frontend:
    build: ./frontend
    depends_on: [backend]
    ports: ["3000:3000"]
```

### Production (recommended)

```
CDN / Load Balancer
        ↓
Frontend (Vercel / Next.js hosting)
        ↓
Backend API (Cloud Run / ECS / Railway)
        ↓
Task Workers (Cloud Run Jobs / ECS Tasks)
        ↓
PostgreSQL + pgvector (Cloud SQL / RDS / Supabase)
        ↓
Redis (Upstash / ElastiCache)
```

---

## 16. Directory Structure

```
photo-discovery-engine/
├── README.md
├── docker-compose.yml
├── .env.example
│
├── backend/
│   ├── app/
│   │   ├── main.py                  — FastAPI app entry point
│   │   ├── config.py                — Config from env vars
│   │   ├── auth/
│   │   │   ├── jwt.py
│   │   │   └── roles.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── ingest.py
│   │   │   │   ├── conversations.py
│   │   │   │   ├── problems.py
│   │   │   │   ├── clusters.py
│   │   │   │   ├── trends.py
│   │   │   │   ├── evidence.py
│   │   │   │   ├── reviews.py
│   │   │   │   ├── research.py
│   │   │   │   └── reports.py
│   │   ├── connectors/
│   │   │   ├── base.py              — BaseConnector abstract class
│   │   │   ├── reddit.py
│   │   │   ├── google_play.py
│   │   │   ├── app_store.py
│   │   │   ├── google_community.py
│   │   │   └── mock.py              — Demo data connector
│   │   ├── pipeline/
│   │   │   ├── cleaning.py          — Dedup, normalize, PII
│   │   │   ├── analysis.py          — LLM relevance + deep analysis
│   │   │   ├── embedding.py         — Embedding generation
│   │   │   ├── clustering.py        — Semantic clustering
│   │   │   ├── problem_discovery.py — Problem synthesis
│   │   │   ├── trend_detection.py   — Time-series trend analysis
│   │   │   └── emerging_detection.py
│   │   ├── models/
│   │   │   ├── providers/
│   │   │   │   ├── base.py          — BaseModelProvider
│   │   │   │   ├── groq.py          — PRIMARY: Groq via OpenAI-compat. API
│   │   │   │   ├── openai.py        — Fallback + embeddings
│   │   │   │   ├── anthropic.py     — Fallback
│   │   │   │   ├── google.py        — Fallback
│   │   │   │   └── local.py         — Ollama fallback
│   │   │   └── router.py            — Model routing logic (default: groq)
│   │   ├── prompts/
│   │   │   ├── photo-retrieval-v1.0.txt
│   │   │   └── photo-retrieval-v1.3.txt
│   │   ├── db/
│   │   │   ├── models.py            — SQLAlchemy ORM models
│   │   │   ├── migrations/          — Alembic migrations
│   │   │   └── seed.py              — Demo data seeding
│   │   ├── worker/
│   │   │   ├── tasks.py             — Celery task definitions
│   │   │   └── scheduler.py         — Periodic job schedules
│   │   └── evaluation/
│   │       ├── benchmark.py
│   │       └── metrics.py
│   ├── tests/
│   │   ├── test_connectors.py
│   │   ├── test_pipeline.py
│   │   ├── test_api.py
│   │   └── test_clustering.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                 — Overview
│   │   ├── problems/
│   │   ├── conversations/
│   │   ├── trends/
│   │   ├── explore/
│   │   ├── review/
│   │   └── evaluation/
│   ├── components/
│   │   ├── ui/
│   │   ├── charts/
│   │   ├── evidence/
│   │   ├── problems/
│   │   ├── conversations/
│   │   ├── assistant/
│   │   └── review/
│   ├── lib/
│   │   ├── api.ts                   — API client
│   │   └── auth.ts                  — Auth helpers
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── Dockerfile
│
└── docs/
    ├── problem.txt                  — Original problem statement
    ├── context.md                   — Summarized context
    └── architecture.md              — This document
```

---

> **Definition of Done:** The MVP is complete when a user can go from raw conversation data to a discovered problem, trace it back to evidence, explore its trend over time, ask the AI research assistant for insights, review AI classifications, and generate a research brief — all within the application, with full evidence traceability.
>
> **Complete loop:** Data → Understanding → Clustering → Problem Discovery → Evidence → Research Insight → Opportunity.
