# Photo Discovery Engine

An AI-powered **Photo Retrieval Discovery Engine** — a research and product-discovery system that continuously analyzes publicly available user conversations from Reddit, YouTube, Google Play, and the App Store to discover, understand, and prioritize the real-world friction and unmet needs people experience when trying to retrieve old, forgotten, or difficult-to-find photos and personal media.

---

## Table of Contents
1. [Architecture & System Flow](#architecture--system-flow)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Local Development)](#quick-start-local-development)
4. [Environment Variables Reference](#environment-variables-reference)
5. [Running Tests](#running-tests)
6. [Developer Guides](#developer-guides)
   - [Adding a New Connector](#adding-a-new-connector)
   - [Adding a New Prompt Version](#adding-a-new-prompt-version)
7. [Definition of Done Verification (14 Items)](#definition-of-done-verification-14-items)
8. [Evidence Limitations & Methodology](#evidence-limitations--methodology)
9. [Documentation Links](#documentation-links)

---

## Architecture & System Flow

```
[ Reddit / YouTube / App Store / Play Store / Demo Data ]
                         │
                         ▼
        ┌───────────────────────────────────┐
        │  Data Ingestion & Connectors Layer│
        │  (Rate limits, SHA-256 PII hash)  │
        └─────────────────┬─────────────────┘
                          │
                          ▼
        ┌───────────────────────────────────┐
        │  Cleaning & Deduplication Layer   │
        │  (HTML strip, ftfy, exact + text) │
        └─────────────────┬─────────────────┘
                          │
                          ▼
        ┌───────────────────────────────────┐
        │  Stage 1: Relevance Classifier    │
        │  (Fast LLM filter: Groq / OpenAI) │
        └─────────────────┬─────────────────┘
                          │ (Relevant only)
                          ▼
        ┌───────────────────────────────────┐
        │  Stage 2: Deep Extraction & Embed │
        │  (Intents, Failures, pgvector)    │
        └─────────────────┬─────────────────┘
                          │
                          ▼
        ┌───────────────────────────────────┐
        │  Clustering & Problem Discovery   │
        │  (DBSCAN, Cross-Source, Trends)   │
        └─────────────────┬─────────────────┘
                          │
                          ▼
        ┌───────────────────────────────────┐
        │  Interactive Next.js Dashboard    │
        │  • Overview & KPI Cards           │
        │  • Discovered Problems & Evidence │
        │  • RAG AI Assistant (/explore)    │
        │  • Human Review (/review)         │
        │  • Model Evaluation (/evaluation) │
        └───────────────────────────────────┘
```

**Key Technologies:**
- **Frontend:** Next.js 14 / 16 (App Router), React, TypeScript, Tailwind CSS, Lucide Icons, Recharts
- **Backend:** Python 3.11+, FastAPI (Async), SQLAlchemy 2.0, Alembic, Pydantic v2
- **Vector Database:** PostgreSQL 16 with `pgvector` (1536-dimensional HNSW cosine index)
- **Task Queue & Cache:** Redis 7 + Celery
- **LLM Engine:** Groq (Llama 3.3 70B, ultra-low latency inference), OpenAI (`gpt-4o-mini`, `text-embedding-3-small`), Anthropic Claude 3.5 Sonnet, Google Gemini 1.5 Pro
- **Authentication:** NextAuth.js + JWT Role-Based Access Control (`admin`, `researcher`, `viewer`)

---

## Prerequisites

| Tool | Minimum Version | Notes |
|---|---|---|
| **Docker Desktop** | 4.x (Compose v2.x) | Required for local container stack |
| **Python** | 3.11 or 3.12 | Required for local virtualenv / tests |
| **Node.js** | 20 LTS (or 22) | Required for Next.js frontend |
| **API Keys** | Groq / Apify / YouTube / OpenAI | Set in `.env` (fallback mock connectors available) |

---

## Quick Start (Local Development)

### 1. Clone & Configure Environment
```bash
git clone <repo-url>
cd "Photo Discovery Engine"
cp .env.example .env
```
*Edit `.env` with your API keys. A complete template is provided in [`.env.example`](.env.example).*

### 2. Start Full Stack with Docker
```bash
docker compose up -d --build
```
This boots:
- **PostgreSQL 16 + pgvector** on `localhost:5432`
- **Redis 7** on `localhost:6379`
- **Backend API (FastAPI)** on `localhost:8000`
- **Celery Worker** (Background pipeline processing)
- **Frontend Dashboard (Next.js)** on `localhost:3000`

### 3. Run Database Migrations
```bash
docker compose exec backend alembic upgrade head
```

### 4. Seed Seed Dataset & Benchmarks
```bash
docker compose exec backend python -m app.db.seed
```
*Seeds 125 realistic conversations across Reddit, YouTube, Google Play, and App Store with 2-year date spread, emerging problem spikes, outlier unknown-unknowns, and 30 ground-truth evaluation benchmark records.*

### 5. Access the Platform
- **Research Dashboard:** [http://localhost:3000](http://localhost:3000)
- **API Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

**Default Seed Accounts:**
- **Admin:** `admin@example.com` / `adminpass123`
- **Researcher:** `researcher@example.com` / `researchpass123`
- **Viewer:** `viewer@example.com` / `viewerpass123`

---

## Environment Variables Reference

See [`.env.example`](.env.example) for the complete reference. Key configurations:

| Variable | Description | Example / Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string with asyncpg | `postgresql+asyncpg://postgres:postgres@db:5432/photo_discovery` |
| `REDIS_URL` | Redis broker and backend for Celery | `redis://redis:6379/0` |
| `JWT_SECRET` | Secret key for HS256 tokens | Random 64-char string |
| `AI_PROVIDER` | Active LLM provider (`groq`, `openai`, `anthropic`, `google`, `mock`) | `groq` |
| `GROQ_API_KEY` | Groq API Key for hardware accelerated Llama 3.3 | `gsk_...` |
| `APIFY_API_TOKEN` | Apify Token for Reddit scraper | `apify_api_...` |
| `YOUTUBE_API_KEY` | YouTube Data API v3 Key | `AIzaSy...` |
| `EMBEDDING_PROVIDER` | Embedding provider (`openai`, `mock`) | `openai` |
| `OPENAI_API_KEY` | OpenAI API Key for embeddings | `sk-...` |

---

## Running Tests

All unit, integration, and contract tests run hermetically using in-memory SQLite and mock model providers without consuming paid API tokens.

### Backend Tests (Pytest)
```bash
cd backend
pytest -v
```
To run specific phases:
```bash
pytest tests/test_phase6.py -v
```

### Frontend Build & Typecheck
```bash
cd frontend
npm run build
```

---

## Developer Guides

### Adding a New Connector

To connect a new data source (e.g. Discourse, Trustpilot, Bluesky):

1. **Create Connector Class:**
   Create `backend/app/connectors/my_source.py` inheriting from `BaseConnector`:
   ```python
   from typing import List, Dict, Any
   from app.connectors.base import BaseConnector, NormalizedRecord

   class MySourceConnector(BaseConnector):
       source_name = "my_source"
       rate_limit_per_minute = 60

       def fetch(self, query: str, since: Any = None, limit: int = 50) -> List[Dict[str, Any]]:
           # Call external API or scraper
           return [{"id": "123", "body": "...", "created_at": "..."}]

       def normalize(self, raw: Dict[str, Any]) -> NormalizedRecord:
           # Map external payload to standard schema
           return NormalizedRecord(
               source=self.source_name,
               external_id=str(raw["id"]),
               text=raw["body"],
               title=raw.get("title", ""),
               url=f"https://example.com/posts/{raw['id']}",
               author_hash=self.hash_author(raw.get("author", "anon")),
               timestamp=self.parse_timestamp(raw.get("created_at")),
               is_demo=False,
           )
   ```

2. **Register Connector in Registry:**
   In `backend/app/connectors/registry.py`:
   ```python
   from app.connectors.my_source import MySourceConnector

   CONNECTOR_REGISTRY["my_source"] = MySourceConnector
   ```

3. **Trigger Ingestion:**
   Call `POST /ingest` with `{ "source": "my_source", "query": "photo search" }`.

---

### Adding a New Prompt Version

The engine uses zero-downtime, file-based prompt versioning with automatic DB registration.

1. **Create Prompt File:**
   Add your new prompt in `backend/app/prompts/`:
   - `relevance-v1.1.txt` (for Stage 1 Relevance)
   - `analysis-v1.2.txt` (for Stage 2 Deep Extraction)

2. **Format Guidelines:**
   - Must contain `{{text}}` placeholder for conversation text.
   - Enforce structured JSON return format matching the schema in `docs/architecture.md §3.4`.

3. **Activate Version:**
   Update `ACTIVE_ANALYSIS_PROMPT_VERSION` or `ACTIVE_RELEVANCE_PROMPT_VERSION` in `app/core/config.py` or `.env`. Every AI analysis row records the exact `prompt_version` used, allowing side-by-side accuracy comparison in the `/evaluation` dashboard.

---

## Definition of Done Verification (14 Items)

All 14 checkpoints specified in `context.md §59` have been implemented and verified:

| # | Checkpoint | Verification Method | Status |
|---|---|---|---|
| **1** | **Load/import conversation data** | Ingestion pipeline supports Reddit (Apify), YouTube Data API v3, Google Play, App Store, and 125-conversation seed dataset. Verified via `POST /ingest` and `seed.py`. | **VERIFIED** |
| **2** | **Process the data with AI** | 2-Stage pipeline: Stage 1 relevance classifier + Stage 2 deep extraction with structured JSON schemas (Groq / OpenAI / Anthropic). | **VERIFIED** |
| **3** | **Search the dataset semantically** | Natural language semantic vector search with pgvector 1536-dim HNSW embeddings at `GET /conversations/search?q=...`. | **VERIFIED** |
| **4** | **See identified user intents** | Categorized into `find_photo`, `find_screenshot`, `find_video`, `cleanup_duplicates`, `troubleshoot_search`, and `album_organization`. Filterable on `/conversations`. | **VERIFIED** |
| **5** | **See memory dimensions** | Visualized on Radar Chart and itemized across temporal, spatial, social, visual, text, and emotional memory anchors. | **VERIFIED** |
| **6** | **See retrieval failure modes** | Ranked Bar Chart and badges identifying OCR failures, unknown dates, false positives, vocabulary mismatches, and temporal drift. | **VERIFIED** |
| **7** | **See automatically generated problem clusters** | Semantic DBSCAN clustering generates cohesive clusters with LLM-synthesized descriptive labels and frequency metrics at `/problems`. | **VERIFIED** |
| **8** | **Open a problem** | Dedicated detail page `/problems/[id]` with 5-dimension score breakdown (frequency, severity, cross-source, evidence diversity, confidence). | **VERIFIED** |
| **9** | **Trace problem back to evidence** | Tab 2 on `/problems/[id]` displays direct citations and verbatim excerpts linking back to original Reddit/YouTube/Store reviews in ≤ 2 clicks. | **VERIFIED** |
| **10** | **Explore trends** | Time-series trend analytics at `/trends` with configurable time horizons (7d, 30d, 90d, 6m, 1y) and platform category heatmaps. | **VERIFIED** |
| **11** | **Discover emerging problem areas** | Emerging surge detection flags velocity > 25% across multiple platforms, highlighted via prominent alert banners and `/trends/emerging`. | **VERIFIED** |
| **12** | **Ask the AI research assistant questions** | Interactive chat UI at `/explore` using grounded RAG retrieval over indexed conversations with inline clickable evidence citations. | **VERIFIED** |
| **13** | **Review/correct AI classifications** | Human-in-the-Loop review queue at `/review` allowing researchers to approve, correct intents, and refine problem taxonomies. | **VERIFIED** |
| **14** | **Generate a research brief** | Modal on `/problems` generates structured executive briefs with 1-click Markdown, JSON, and CSV export. | **VERIFIED** |

---

## Evidence Limitations & Methodology

The application includes an **Evidence Limitations Panel** on the Overview dashboard emphasizing research caveats:
1. **Non-Statistical Representativeness:** Captures authentic qualitative friction and unprompted user expressions across public community channels, but does not represent a population census or market survey.
2. **Platform Sampling Biases:**
   - **Reddit / Tech Forums:** Skew toward power users, edge-case camera gear, and complex multi-device sync friction.
   - **App Store & Google Play:** Skew toward acute dissatisfaction, search syntax failures, and update regressions.
   - **YouTube Comments:** Skew toward feature discovery, tutorial gaps, and aspirational workflows.
3. **Probabilistic Classifications:** All AI annotations, memory dimensions, and confidence scores are probabilistic model inferences. All synthetic demo records feature a prominent `DEMO DATA` watermark badge.

---

## Documentation Links

- [System Context & Requirements](docs/context.md)
- [System Architecture](docs/architecture.md)
- [Implementation Plan & Phase Checklists](docs/implementation-plan.md)
- [Edge Cases & Error Handling Guide](docs/edge-cases.md)
