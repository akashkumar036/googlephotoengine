# Phase-Wise Implementation Plan
## AI-Powered Photo Retrieval Discovery Engine

> **Based on:** `docs/context.md` · `docs/architecture.md`
> **Generated:** 2026-10-02

---

## Overview

This plan breaks the build into **6 sequential phases**, each delivering a testable, runnable increment. Every phase ends with a clear **exit criterion** — a set of things that must work before the next phase begins.

| Phase | Name | Duration (est.) | Deliverable |
|---|---|---|---|
| 1 | Foundation & Project Setup | 1–2 days | Runnable scaffold with DB, auth, and CI |
| 2 | Data Ingestion & Normalization | 3–5 days | Data flowing into PostgreSQL from connectors |
| 3 | AI Analysis Pipeline | 5–7 days | Conversations classified and embedded |
| 4 | Clustering & Problem Discovery | 4–5 days | Semantic clusters and problems in DB |
| 5 | Dashboard & Frontend | 5–7 days | Full 6-page research dashboard live |
| 6 | Polish, Evaluation & Launch | 3–4 days | Seed data, tests, docs, definition of done met |

**Total estimated range:** 21–30 engineering days

---

## Phase 1 — Foundation & Project Setup

**Goal:** Create the monorepo skeleton, configure Docker, stand up PostgreSQL with pgvector, implement authentication, and verify every layer can talk to every other layer.

---

### 1.1 Monorepo Initialization

**Tasks:**
- [ ] Create root `photo-discovery-engine/` directory
- [ ] Initialize git repository, add `.gitignore`, `README.md`
- [ ] Create directory structure:
  ```
  photo-discovery-engine/
  ├── backend/
  ├── frontend/
  ├── docs/
  ├── docker-compose.yml
  └── .env.example
  ```

**Acceptance:** `git status` shows clean working tree with scaffold committed.

---

### 1.2 Docker Compose Environment

**Tasks:**
- [ ] Write `docker-compose.yml` with services:
  - `db` — `pgvector/pgvector:pg16` on port `5432`
  - `redis` — `redis:7-alpine` on port `6379`
  - `backend` — FastAPI app, port `8000`
  - `worker` — Celery worker (same image, different command)
  - `frontend` — Next.js, port `3000`
- [ ] Write `.env.example` with all required variables (see §13 in `architecture.md`)
- [ ] Verify all services start cleanly: `docker compose up`

**Acceptance:** `docker compose ps` shows all 5 services healthy.

---

### 1.3 Backend Scaffold (FastAPI)

**Tasks:**
- [ ] Initialize Python project: `pyproject.toml` or `requirements.txt`
- [ ] Install core dependencies:
  - `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `psycopg2-binary`
  - `pgvector`, `celery`, `redis`, `pydantic`, `python-jose`, `passlib`
- [ ] Create `app/main.py` with FastAPI app instance
- [ ] Create `app/config.py` — load all settings from env vars using Pydantic `BaseSettings`
- [ ] Add health check endpoint: `GET /health → { "status": "ok" }`
- [ ] Add structured JSON logging middleware

**Acceptance:** `GET http://localhost:8000/health` returns `200 OK`.

---

### 1.4 Database Setup & Migrations

**Tasks:**
- [ ] Initialize Alembic: `alembic init migrations`
- [ ] Configure `alembic.ini` to use `DATABASE_URL` from env
- [ ] Enable pgvector extension in migration:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```
- [ ] Create initial migration with all 13 tables from `architecture.md §5`:
  - `sources`, `conversations`, `ai_analyses`
  - `clusters`, `cluster_memberships`
  - `problems`, `evidence`, `opportunities`, `trends`
  - `human_reviews`, `users`, `jobs`
  - `prompt_versions`, `research_reports`, `evaluation_benchmarks`
- [ ] Run migration: `alembic upgrade head`
- [ ] Add HNSW index on `conversations.embedding`:
  ```sql
  CREATE INDEX ON conversations USING hnsw (embedding vector_cosine_ops);
  ```

**Acceptance:** All tables exist in DB; `alembic current` shows latest revision.

---

### 1.5 Authentication & RBAC

**Tasks:**
- [ ] Implement user model and password hashing (`passlib` / bcrypt)
- [ ] Implement JWT issue + verify utilities (`python-jose`)
- [ ] Create endpoints:
  - `POST /auth/login` — returns `{ access_token, refresh_token }`
  - `POST /auth/refresh` — rotate access token
  - `GET /auth/me` — returns current user
- [ ] Create RBAC middleware — `require_role("admin" | "researcher" | "viewer")`
- [ ] Apply role guard to all subsequent routes
- [ ] Seed one `admin` user from env vars on startup

**Acceptance:** Login returns valid JWT; protected endpoint returns `401` without token; `403` with wrong role.

---

### 1.6 Frontend Scaffold (Next.js)

**Tasks:**
- [ ] Bootstrap: `npx create-next-app@latest ./frontend --typescript --tailwind --app`
- [ ] Install dependencies: `axios`, `recharts`, `lucide-react`, `@radix-ui/react-*`, `next-auth`
- [ ] Configure `next-auth` with credentials provider pointing to backend JWT
- [ ] Create global layout: sidebar nav with 6 page links + user avatar
- [ ] Create placeholder pages for all 6 routes:
  - `/` Overview, `/problems`, `/conversations`, `/trends`, `/explore`, `/review`
- [ ] Create `lib/api.ts` — Axios client with auth header injection and base URL from env

**Acceptance:** `npm run dev` starts; all 6 pages render without errors; login flow works.

---

### 1.7 Background Job Worker (Celery)

**Tasks:**
- [ ] Configure Celery with Redis broker and PostgreSQL result backend
- [ ] Create `app/worker/tasks.py` with a smoke-test task:
  ```python
  @app.task
  def ping():
      return "pong"
  ```
- [ ] Verify task executes: `celery -A app.worker call worker.tasks.ping`

**Acceptance:** Celery worker logs show task received and completed.

---

### Phase 1 Exit Criteria

- [ ] All Docker services start with `docker compose up`
- [ ] `GET /health` returns `200`
- [ ] Database has all tables with correct schema
- [ ] Login/auth flow works end-to-end
- [ ] All 6 frontend pages render (placeholder content is fine)
- [ ] Celery worker processes a test task
- [ ] No secrets in any committed file

---

## Phase 2 — Data Ingestion & Normalization

**Goal:** Build the connector layer, normalization pipeline, deduplication, and the ingestion job system. Data must flow from at lea### 2.1 Base Connector Interface

**Tasks:**
- [x] Create `app/connectors/base.py`:
  ```python
  class BaseConnector(ABC):
      source_name: str
      rate_limit_per_minute: int = 60

      @abstractmethod
      def fetch(self, query, since, limit) -> List[dict]: ...

      @abstractmethod
      def normalize(self, raw) -> dict: ...

      def run(self, query, since, limit) -> List[dict]:
          raw = self.fetch(query, since, limit)
          return [self.normalize(r) for r in raw]
  ```
- [x] Define `NormalizedRecord` Pydantic model matching the schema from `architecture.md §3.4`
- [x] Define `RawRecord` base type

**Acceptance:** `BaseConnector` raises `NotImplementedError` on unimplemented methods.

---

### 2.2 Mock / Demo Connector

Build this **first** so all downstream pipeline work can be tested without real API access.

**Tasks:**
- [x] Create `app/connectors/mock.py` — `MockConnector(BaseConnector)`
- [x] Create `data/demo_dataset.json` with 50–100 realistic conversations covering:
  - All intent types (find photo, find screenshot, find video, etc.)
  - All memory dimensions (temporal, spatial, social, visual, event, text, emotional)
  - All failure modes (unknown date, OCR failure, poor ranking, etc.)
  - Multiple sources (reddit, google_play, app_store, google_community)
  - A 2-year date range (for trend detection)
  - Emerging problems (spike in last 30 days)
- [x] Tag all records with `"is_demo": true` and display label `"DEMO DATA"`
- [x] Connector loads and normalizes demo dataset

**Acceptance:** `MockConnector().run(...)` returns 50+ valid `NormalizedRecord` objects.

---

### 2.3 Reddit Connector

**Tasks:**
- [x] Install `praw` (Python Reddit API Wrapper)
- [x] Create `app/connectors/reddit.py` — `RedditConnector(BaseConnector)`
- [x] Authenticate via Reddit OAuth2 (client ID + secret from env)
- [x] Implement `fetch()`:
  - Search target subreddits: `googlephotos`, `iphone`, `androidquestions`, `techsupport`, `ApplePhotos`
  - Search terms: `"find photo"`, `"lost photo"`, `"can't find"`, `"photo retrieval"`, `"searching for memory"`
  - Fetch posts + top-level comments
- [x] Implement `normalize()` — map Reddit `Submission` + `Comment` fields to `NormalizedRecord`
- [x] Respect Reddit API rate limits (60 req/min max)
- [x] Hash `author` field before storage

**Acceptance:** `RedditConnector().run("find photo", ...)` returns normalized records; author is hashed.

---

### 2.4 Google Play Connector

**Tasks:**
- [x] Install `google-play-scraper`
- [x] Create `app/connectors/google_play.py` — `GooglePlayConnector(BaseConnector)`
- [x] Target apps: `com.google.android.apps.photos`, and related photo apps
- [x] Implement `fetch()` — paginated review fetch with language/country params
- [x] Implement `normalize()` — map review fields to `NormalizedRecord`
- [x] Handle rate limiting gracefully (exponential backoff)

**Acceptance:** `GooglePlayConnector().run(...)` returns normalized review records.

---

### 2.5 App Store Connector

**Tasks:**
- [x] Install `app-store-scraper`
- [x] Create `app/connectors/app_store.py` — `AppStoreConnector(BaseConnector)`
- [x] Target apps: Google Photos iOS (`id=962194608`), Apple Photos, etc.
- [x] Implement `fetch()` and `normalize()`

**Acceptance:** `AppStoreConnector().run(...)` returns normalized review records.

---

### 2.6 Source Registry

**Tasks:**
- [x] Create `app/connectors/registry.py`:
  ```python
  CONNECTOR_REGISTRY = {
      "reddit": RedditConnector,
      "google_play": GooglePlayConnector,
      "app_store": AppStoreConnector,
      "demo": MockConnector,
  }
  ```
- [x] Add `sources` table seed data for each registered source

**Acceptance:** New connector can be added to registry without touching other code.

---

### 2.7 Cleaning & Normalization Pipeline

**Tasks:**
- [x] Create `app/pipeline/cleaning.py`
- [x] Implement the following steps in sequence:

  | Step | Implementation |
  |---|---|
  | HTML/markup removal | `beautifulsoup4` or regex |
  | Whitespace normalization | regex strip |
  | Encoding normalization | `ftfy` library |
  | Language detection | `langdetect` or `lingua-language-detector` |
  | Spam/ad detection | keyword blocklist + length heuristics |
  | Low-information filter | min token count threshold |
  | Quoted content identification | regex for `>` prefixes, `"..."` patterns |
  | PII detection | `presidio-analyzer` or regex for emails, phone numbers |
  | Author anonymization | SHA-256 hash of author string |

- [x] Preserve original `text` field; write cleaned version to `cleaned_text`
- [x] Flag records: `is_cleaned=True`, `language`, `is_spam`, `pii_detected`

**Acceptance:** Cleaning pipeline processes a batch of 100 records without error; PII not stored raw.

---

### 2.8 Deduplication System

**Tasks:**
- [x] Create `app/pipeline/deduplication.py`
- [x] **Exact dedup:** Compute `SHA-256(source + source_id)` — mark as `duplicate` if hash exists
- [x] **Content hash dedup:** Compute `SHA-256(normalized_text)` — mark as `duplicate` if text hash exists
- [x] **Semantic near-dedup** (post-embedding):
  - After embeddings generated, run cosine similarity check
  - Records with similarity > `DEDUP_SIMILARITY_THRESHOLD` (default: 0.95) → `possible_duplicate`
- [x] Store dedup status: `original | duplicate | possible_duplicate | cross_post`
- [x] **Never** inflate problem frequency with duplicates — exclude non-originals from analysis counts

**Acceptance:** Re-running ingestion on the same source does not create new records for existing `source_id`s.

---

### 2.9 Ingestion Job & API

**Tasks:**
- [x] Create Celery task `ingest_source`:
  ```python
  @celery.task(bind=True, max_retries=3)
  def ingest_source(self, source_name, query, since, limit):
      connector = CONNECTOR_REGISTRY[source_name]()
      records = connector.run(query, since, limit)
      for record in records:
          deduplicate_and_store(record)
      enqueue_cleaning_batch(record_ids)
  ```
- [x] Create `POST /ingest` API endpoint:
  - Required role: `researcher` or `admin`
  - Enqueues `ingest_source` task, returns `{ job_id }`
- [x] Create `GET /jobs/:id` endpoint — returns job status from DB
- [x] Create `GET /jobs` endpoint — list all jobs (paginated)
- [x] Persist job status updates (`queued → running → done | failed`) in `jobs` table

**Acceptance:** `POST /ingest { "source": "demo" }` returns a `job_id`; polling `GET /jobs/:id` shows progress; records appear in `conversations` table.

---

### Phase 2 Exit Criteria

- [x] Demo connector loads 50+ records into DB
- [x] At least 1 real connector (Reddit or Play Store) fetches live data
- [x] All records pass through cleaning pipeline
- [x] Deduplication prevents re-inserting existing records
- [x] Job status is trackable via API
- [x] `GET /conversations` returns paginated, filterable list
- [x] No PII stored in raw form

---

## Phase 3 — AI Analysis Pipeline

**Goal:** Build the two-stage LLM classification pipeline, generate embeddings, store structured `AIAnalysis` per conversation, and implement prompt versioning.

---

### 3.1 Model Abstraction Layer

**Tasks:**
- [x] Create `app/models/providers/base.py`:
  ```python
  class BaseModelProvider(ABC):
      @abstractmethod
      def classify(self, text: str, prompt: str) -> dict: ...

      @abstractmethod
      def embed(self, texts: List[str]) -> List[List[float]]: ...
  ```
- [x] Implement `app/models/providers/openai.py` — `OpenAIProvider`
  - `classify()` → `openai.chat.completions.create()`
  - `embed()` → `openai.embeddings.create()`
- [x] Implement `app/models/providers/anthropic.py` — `AnthropicProvider`
- [x] Implement `app/models/providers/google.py` — `GoogleProvider`
- [x] Create `app/models/router.py`:
  - Reads `AI_PROVIDER` from config
  - Returns the correct provider instance
  - Applies Stage 1 vs Stage 2 model routing logic

**Acceptance:** Swapping `AI_PROVIDER=anthropic` in `.env` uses Claude without code changes.

---

### 3.2 Prompt Registry

**Tasks:**
- [x] Create `app/prompts/` directory with versioned prompt files:
  - `relevance-v1.0.txt` — Stage 1 relevance classification prompt
  - `analysis-v1.0.txt` — Stage 2 deep analysis prompt
- [x] Store prompt versions in `prompt_versions` table on startup
- [x] Create `app/prompts/loader.py` — load prompt by version string
- [x] Every AI call records the `prompt_version` used

**Stage 1 relevance prompt structure:**
```
System: You are a photo retrieval research classifier.
Task: Determine if the following conversation is relevant to a user
trying to find, retrieve, or search for photos, videos, or screenshots
from their personal library. Return JSON only.

Output format:
{
  "relevance_score": float (0-1),
  "is_relevant": boolean,
  "reasoning": string
}

Conversation:
{{text}}
```

**Stage 2 deep analysis prompt structure:**
```
System: You are a photo retrieval UX research analyst.
Task: Extract structured retrieval problem data from this conversation.
Be precise. Only extract what is evidenced in the text. Return JSON only.

Output format: (full AIAnalysis schema)

Conversation:
{{text}}
```

**Acceptance:** Both prompts load by version string; changing prompt text increments version.

---

### 3.3 Stage 1 — Relevance Filter Job

**Tasks:**
- [x] Create Celery task `analyze_relevance_batch(conversation_ids: List[str])`
- [x] For each conversation:
  - Call Stage 1 model with relevance prompt
  - Store `relevance_score`, `is_relevant` in `ai_analyses` table
  - If `is_relevant = False`: mark conversation, skip Stage 2
- [x] Implement batching: group conversations into batches of `BATCH_SIZE` (default: 20)
- [x] Implement retry with exponential backoff on API errors
- [x] Log token usage per batch for cost tracking

**Acceptance:** Batch of 50 demo conversations produces `is_relevant` flags; irrelevant records are skipped correctly.

---

### 3.4 Stage 2 — Deep Analysis Job

**Tasks:**
- [x] Create Celery task `analyze_deep_batch(conversation_ids: List[str])`
- [x] For each relevant conversation:
  - Call Stage 2 model with analysis prompt
  - Parse JSON response into `AIAnalysis` Pydantic model
  - Store full analysis in `ai_analyses` table
- [x] Handle JSON parsing errors gracefully (log + skip, don't crash batch)
- [x] Cache: skip re-analysis if `(conversation_id, prompt_version)` already exists in DB
- [x] Store `model_provider`, `model_name`, `prompt_version`, `processed_at`

**Acceptance:** 50 relevant demo conversations have complete `ai_analyses` rows with all fields populated.

---

### 3.5 Embedding Generation Job

**Tasks:**
- [x] Create Celery task `embed_batch(conversation_ids: List[str])`
- [x] For each analyzed conversation:
  - Concatenate `title + " " + cleaned_text` as embedding input
  - Call embedding model API (batched — up to 100 texts per API call)
  - Store `VECTOR(1536)` in `conversations.embedding`
- [x] Skip if embedding already exists (reuse)
- [x] After bulk embedding complete, trigger HNSW index refresh

**Acceptance:** `conversations.embedding` is non-null for all relevant records; `pgvector` cosine similarity query returns results.

---

### 3.6 Analysis Pipeline Orchestration

**Tasks:**
- [x] Create master Celery chain: `ingest → clean → relevance → deep → embed`
- [x] Each stage automatically enqueues the next on completion
- [x] Job status updates propagate through each stage
- [x] Create `POST /pipeline/run` endpoint to trigger full pipeline on a source

**Acceptance:** A single API call to `POST /pipeline/run { "source": "demo" }` runs the entire pipeline end-to-end.

---

### 3.7 Conversation API (with AI annotations)

**Tasks:**
- [x] Update `GET /conversations` to join with `ai_analyses`:
  - Include: `primary_intent`, `memory_types`, `failure_modes`, `confidence`, `is_relevant`
- [x] Update `GET /conversations/:id` to return full `AIAnalysis` JSON
- [x] Add filter params: `intent`, `memory_type`, `failure_mode`, `confidence_min`, `is_relevant`

**Acceptance:** API returns conversations with full AI annotations; filters work correctly.

---

### Phase 3 Exit Criteria

- [x] All demo conversations have `is_relevant` flag set
- [x] All relevant conversations have complete `AIAnalysis` in DB
- [x] All relevant conversations have non-null `embedding` vector
- [x] Model provider is configurable via env var (no code change)
- [x] Prompt version is stored on every analysis record
- [x] Re-running analysis on same record reuses cached result
- [x] `GET /conversations/:id` returns full AI annotation

---

## Phase 4 — Clustering & Problem Discovery

**Goal:** Run semantic clustering over embeddings, synthesize discovered problems, link evidence, detect trends, and surface emerging problems.

---

### 4.1 Semantic Clustering Job

**Tasks:**
- [x] Create `app/pipeline/clustering.py`
- [x] Implement clustering algorithm:
  ```python
  def cluster_conversations():
      # 1. Load all embeddings from pgvector
      # 2. Run DBSCAN (or HNSW + DBSCAN hybrid)
      # 3. Assign cluster labels
      # 4. For each cluster, generate AI label using LLM
      # 5. Store cluster in `clusters` table
      # 6. Store memberships in `cluster_memberships` table
  ```
- [x] Use configurable `CLUSTERING_ALGORITHM` (`dbscan` default)
- [x] DBSCAN params: `CLUSTER_EPSILON`, `CLUSTER_MIN_SAMPLES` from config
- [x] For outlier conversations (DBSCAN label = -1): flag for "unknown unknowns" detection
- [x] Generate cluster label via LLM: *"In one sentence, what photo retrieval problem do these conversations share?"*

**Acceptance:** After clustering 50+ conversations, `clusters` table has ≥ 5 distinct clusters; each cluster has an AI-generated label.

---

### 4.2 Problem Discovery Job

**Tasks:**
- [x] Create `app/pipeline/problem_discovery.py`
- [x] For each cluster (or group of high-similarity clusters):
  - Sample up to 10 representative conversations
  - Prompt LLM: synthesize a structured `Problem` record
  - Calculate composite scores:
    - `frequency` = conversation count in cluster
    - `source_count` = distinct sources represented
    - `frustration_score` = mean `frustration_level` from ai_analyses
    - `severity_score` = mean `severity`
    - `cross_source_score` = source_count / total sources
    - `evidence_diversity_score` = source entropy
    - `confidence` = mean `confidence` of member analyses
  - Create or update `problems` table row
- [x] Create `evidence` links: one row per supporting conversation
- [x] Create initial `opportunities` records from LLM-suggested opportunity areas

**Acceptance:** `problems` table has at least 5 rows; each has ≥ 3 evidence links; scores are populated.

---

### 4.3 Taxonomy Assignment

**Tasks:**
- [x] Create `app/pipeline/taxonomy.py`
- [x] Implement taxonomy assignment:
  - For each problem, assign 1–3 taxonomy categories from the predefined list (see `context.md §13`)
  - LLM assigns categories; if none fit well, flag as `"Other"` + generate a proposed new category name
- [x] Store proposed new categories in a separate `taxonomy_proposals` table requiring admin approval
- [x] Create `GET /taxonomy` endpoint listing all categories + proposal count

**Acceptance:** Every problem has at least one taxonomy category; proposed new categories require admin approval before use.

---

### 4.4 Trend Detection

**Tasks:**
- [x] Create `app/pipeline/trend_detection.py`
- [x] For each problem:
  - Group its linked conversations by time bucket (week/month)
  - Calculate conversation count per bucket
  - Calculate `growth_rate` = (current period count − prior period count) / prior period count
  - Store in `trends` table
- [x] Schedule trend recalculation as a periodic Celery beat task (daily)
- [x] Create `GET /trends` API endpoint:
  - Query params: `period` (`7d | 30d | 90d | 6m | 1y`), `granularity` (`day | week | month`)
  - Returns: `{ problem_id, label, data_points: [{ date, count }], growth_rate }`

**Acceptance:** `GET /trends?period=30d` returns time-series data for each problem with growth rates.

---

### 4.5 Emerging Problem Detection

**Tasks:**
- [x] Create `app/pipeline/emerging_detection.py`
- [x] Define "emerging" as:
  - Problem `growth_rate > EMERGING_PROBLEM_GROWTH_THRESHOLD` (default: 25%)
  - AND appearing in ≥ 2 sources
  - AND `frequency > 5`
- [x] Set `problems.is_emerging = True` for qualifying problems
- [x] Generate an "Emerging Problem Alert" record with:
  - Why it is emerging (evidence)
  - First observed date
  - Growth rate
  - Sources
  - Confidence
- [x] New emerging problems require human approval (`is_approved = False` until reviewed)
- [x] Create `GET /trends/emerging` endpoint returning current emerging problem alerts

**Acceptance:** At least 1 problem in demo dataset is flagged as emerging; it appears in `GET /trends/emerging`.

---

### 4.6 Unknown Unknowns Detection

**Tasks:**
- [x] Identify all outlier conversations (DBSCAN label = -1 or similarity < 0.4 to nearest cluster)
- [x] Run BERTopic or LDA over outlier embeddings to find sub-patterns
- [x] For each detected outlier pattern:
  - Prompt LLM: *"What recurring user problem do these outlier conversations share that doesn't fit our current taxonomy?"*
  - Generate a `taxonomy_proposals` record
  - Notify researchers via dashboard alert
- [x] Run as periodic job (weekly)

**Acceptance:** Outlier conversations are identifiable; at least 1 taxonomy proposal generated from demo data.

---

### 4.7 Cross-Platform Comparison

**Tasks:**
- [x] For each problem, group its evidence by `source`
- [x] Expose `GET /problems/:id/cross-platform`:
  ```json
  {
    "problem_id": "...",
    "title": "...",
    "platform_breakdown": {
      "reddit": { "count": 42, "excerpts": [...] },
      "google_play": { "count": 18, "excerpts": [...] }
    }
  }
  ```
- [x] Detect if a problem is **isolated** (1 source) or **widespread** (≥ 3 sources)

**Acceptance:** Cross-platform breakdown is available per problem; isolation flag is set correctly.

---

### 4.8 Problem & Cluster APIs

**Tasks:**
- [x] `GET /problems` — paginated, filterable by taxonomy, source, severity, growth, emerging flag
- [x] `GET /problems/:id` — full problem record with evidence, trends, opportunities, cross-platform data
- [x] `GET /clusters` — list clusters with member count and label
- [x] `GET /clusters/:id` — cluster detail with representative conversations
- [x] `GET /evidence/:id` — evidence record with full conversation context

**Acceptance:** All endpoints return well-structured JSON; filtering works correctly.

---

### Phase 4 Exit Criteria

- [x] Clustering produces ≥ 5 distinct, labeled clusters
- [x] Problem discovery synthesizes ≥ 5 problems with full evidence chains
- [x] Every problem has taxonomy categories assigned
- [x] Trend data is available for all problems
- [x] At least 1 emerging problem is flagged and detectable
- [x] Outlier conversations are identified and surface as taxonomy proposals
- [x] All problem and cluster APIs return correct data

---

## Phase 5 — Dashboard & Frontend

**Goal:** Build the complete 6-page research dashboard, AI research assistant, human review UI, evidence viewer, and research brief generator.

---

### 5.1 Design System

**Tasks:**
- [x] Configure Tailwind CSS theme: colors, typography, spacing, shadows
- [x] Install and configure Google Font (Inter or Outfit)
- [x] Create `components/ui/` primitive components:
  - `Button`, `Card`, `Badge`, `Input`, `Select`, `Textarea`
  - `Modal`, `Drawer`, `Tooltip`, `Tabs`
  - `Spinner`, `EmptyState`, `ErrorBoundary`
- [x] Create `components/charts/`:
  - `TimeSeriesChart` (Recharts `LineChart`)
  - `RadarChart` (memory dimensions)
  - `BarChart` (failure modes, source distribution)
  - `DonutChart` (source breakdown)
- [x] Create global `Sidebar` + `TopNav` layout components

**Acceptance:** All UI primitives render in Storybook or a `/design` route.

---

### 5.2 Page 1 — Overview (`/`)

**Widgets to build:**

| Widget | Data source |
|---|---|
| Stats bar (6 KPI cards) | `GET /stats` (new aggregate endpoint) |
| Top Problems table | `GET /problems?sort=frequency&limit=10` |
| Emerging Alerts panel | `GET /trends/emerging` |
| Memory Dimension radar chart | Aggregate from `ai_analyses.memory_types` |
| Retrieval Failure bar chart | Aggregate from `ai_analyses.failure_modes` |
| Source distribution donut | Aggregate from `conversations.source` |
| Recent activity feed | `GET /jobs?limit=10` + recent problems |

**Tasks:**
- [x] Create `GET /stats` backend endpoint returning all overview aggregates
- [x] Build and wire all 7 widgets
- [x] Add loading skeletons and empty states

**Acceptance:** Overview page loads in < 2 seconds; all widgets show real demo data.

---

### 5.3 Page 2 — Problems (`/problems`)

**Tasks:**
- [x] Build `ProblemFilters` sidebar:
  - Source multi-select
  - Taxonomy category filter
  - Memory type filter
  - Failure mode filter
  - Date range picker
  - Minimum confidence slider
  - Emerging only toggle
- [x] Build `ProblemCard` component:
  - Title, statement excerpt, frequency, growth badge, source count, severity indicator, taxonomy tags
- [x] Implement client-side filter state synchronized to URL query params
- [x] Paginated list with infinite scroll or numbered pagination
- [x] Search box: filter by problem title / keywords

**Acceptance:** Problems page loads, filters update results in real time, URL params are shareable.

---

### 5.4 Page 3 — Problem Detail (`/problems/:id`)

**Tasks:**
- [x] Build layout: header (title + scores), tabbed content
- [x] **Tab 1 — Overview:**
  - Frequency, sources, growth rate, user segments
  - Multi-dimension score bars (frequency / severity / cross-source / evidence diversity / confidence)
  - Common memory signals
  - Typical queries list
  - Failure modes
- [x] **Tab 2 — Evidence:**
  - `EvidenceCard` list: source icon, date, excerpt, extracted intent, memory types, AI confidence
  - "Show original context" expandable section
  - Link to full conversation
- [x] **Tab 3 — Trends:**
  - `TimeSeriesChart` for this problem (period selector: 7d / 30d / 90d / 6m / 1y)
  - Growth vs. prior period indicator
- [x] **Tab 4 — Cross-Platform:**
  - Platform breakdown cards with representative quotes per platform
- [x] **Tab 5 — Opportunities:**
  - Observed problem → Underlying need → Opportunity → Hypothesis (labeled)
  - Explicitly mark solution hypotheses as "Hypothesis — not validated"

**Acceptance:** All tabs render with data; evidence cards show real conversations; hypothesis labels are visible.

---

### 5.5 Page 4 — Conversations (`/conversations`)

**Tasks:**
- [x] Build `ConversationCard` component:
  - Source badge, date, title, text excerpt, engagement stats
  - `AnnotationOverlay`: intent tag, memory type badges, failure mode badges, confidence ring
  - DEMO DATA watermark for demo records
- [x] Implement filter panel (source, intent, memory type, failure mode, language, date range)
- [x] Full-text search box (calls `GET /conversations?q=...`)
- [x] Click-through to full conversation view with complete AI annotation

**Acceptance:** All conversations visible; DEMO DATA label shows on mock records; filters work.

---

### 5.6 Page 5 — Trends (`/trends`)

**Tasks:**
- [x] Global period selector (7d / 30d / 90d / 6m / 1y / custom)
- [x] Top trends table: problem + current frequency + growth + trend sparkline
- [x] `TimeSeriesChart` overlay: compare up to 5 problems on one chart
- [x] Emerging problems section with alert cards (growth rate + first seen date)
- [x] Taxonomy heatmap: categories × time (shows which categories are growing)

**Acceptance:** Trend charts render with real time-series data; period selector updates all charts.

---

### 5.7 Page 6 — Explore / AI Research Assistant (`/explore`)

**Tasks:**
- [x] Build chat-style UI with message history
- [x] User types a natural-language research question
- [x] `POST /research/query` is called on submit
- [x] Render structured response:
  - Answer paragraph (with inline citations)
  - Evidence cards (expandable)
  - Related problems list
  - Confidence indicator
  - "Answer type" badge: `Evidence-grounded | Interpretation | Hypothesis`
- [x] Conversation history persists in component state (session)
- [x] Suggested starter questions displayed on empty state:
  - "What are the most common reasons people fail to find old photos?"
  - "Which failure modes are increasing the fastest?"
  - "Give me 10 unmet needs related to forgotten photos."

**Acceptance:** Typing a research question returns a grounded answer with clickable evidence links.

---

### 5.8 Human Review Page (`/review`)

**Tasks:**
- [x] Build review queue: list of `pending` AI classifications awaiting review
- [x] `ReviewCard` component per item:
  - Original AI classification shown
  - Fields: intent, memory types, failure modes (editable dropdowns)
  - Actions: Approve / Correct / Mark irrelevant / Bookmark / Add note
- [x] Inline cluster actions: Merge cluster / Split cluster / Rename
- [x] Taxonomy management panel: view all categories, add/edit, approve proposals
- [x] Submit review → `POST /reviews`
- [x] Queue count shown in sidebar nav badge

**Acceptance:** Researcher can approve, correct, and annotate AI classifications; corrections persist in DB.

---

### 5.9 Research Brief Generator

**Tasks:**
- [x] Add "Generate Brief" button to Problems page and Problem Detail page
- [x] Modal to configure brief scope (select problems, time period, source filter)
- [x] Call `POST /reports` → backend generates structured brief using LLM
- [x] Display generated brief inline with sections:
  - Executive Summary, Key Problems, Failure Modes, Memory Models, Quotes, Trends, Unmet Needs, Opportunities, Open Questions
- [x] Export buttons: **Download Markdown** / **Download JSON** / **Download CSV**

**Acceptance:** Full research brief generates in < 30 seconds; Markdown export is valid and readable.

---

### 5.10 RAG Search (Backend)

**Tasks:**
- [x] Create `app/pipeline/research_assistant.py`
- [x] Implement RAG flow:
  ```
  1. Embed user query
  2. pgvector ANN search → top-20 similar conversations
  3. Assemble context: excerpts + metadata
  4. LLM call with grounded prompt: "Answer using ONLY the provided evidence"
  5. Parse answer + evidence citations
  6. Return structured response
  ```
- [x] Distinguish answer types in response: `evidence_grounded | interpretation | hypothesis`
- [x] Every factual claim must have ≥ 1 evidence link

**Acceptance:** RAG query returns grounded answer with real evidence citations; fabricated answers are not returned.

---

### 5.11 Natural-Language Search (Dataset)

**Tasks:**
- [x] Create `GET /conversations/search?q=<NL query>` endpoint
- [x] Embed the query, ANN search in pgvector, return ranked conversation results
- [x] Results show similarity score + highlighted relevant excerpt
- [x] Wire to a search bar in the Conversations page

**Acceptance:** Searching "users who couldn't find photos from a wedding" returns semantically relevant conversations.

---

### Phase 5 Exit Criteria

- [x] All 6 pages render with real data (no hardcoded values)
- [x] Insight → Evidence navigation works in ≤ 2 clicks
- [x] AI research assistant returns grounded answers
- [x] Human review workflow saves to DB
- [x] Research brief generates and exports as Markdown
- [x] DEMO DATA watermark visible on all mock records
- [x] No API keys visible in browser / network tab

---

## Phase 6 — Polish, Evaluation & Launch

**Goal:** Finalize the seed dataset, build the evaluation framework, write tests, complete documentation, and verify all 14 "Definition of Done" items from `context.md §59`.

---

### 6.1 Seed Dataset Finalization

**Tasks:**
- [x] Expand demo dataset to 100–200 conversations
- [x] Ensure coverage:
  - ≥ 5 taxonomy categories represented
  - ≥ 3 sources represented
  - 2-year date spread
  - At least 2 emerging problems
  - At least 3 distinct clusters
  - At least 1 cross-platform problem (≥ 3 sources)
  - At least 5 "unknown unknowns" outlier conversations
- [x] All demo records have `"is_demo": true` and UI shows **DEMO DATA** badge
- [x] Create DB seeding script: `python -m app.db.seed`
- [x] Full pipeline runs on seed data in < 5 minutes

**Acceptance:** Fresh `docker compose up` + `python -m app.db.seed` + pipeline run → all dashboard pages show meaningful data.

---

### 6.2 Evaluation Framework

**Tasks:**
- [x] Manually label 30 conversations as a benchmark dataset:
  - Ground truth: `is_relevant`, `primary_intent`, `failure_modes`
- [x] Store in `evaluation_benchmarks` table
- [x] Create `app/evaluation/metrics.py`:
  - Relevance accuracy (precision / recall / F1)
  - Intent accuracy (% correct)
  - Failure-mode accuracy (% correct)
  - Hallucination rate (manual review metric)
- [x] Create `GET /evaluation/results` endpoint (admin only)
- [x] Build `/evaluation` page in frontend:
  - Model performance table
  - Per-metric scores
  - Prompt version comparison

**Acceptance:** Evaluation page shows accuracy metrics for the benchmark dataset.

---

### 6.3 Feedback Learning Loop

**Tasks:**
- [x] Create `app/pipeline/feedback.py`
- [x] When human corrections accumulate (≥ 50 corrections):
  - Export correction data as evaluation examples
  - Automatically test against benchmark: does new prompt perform better?
- [x] Store all corrections in `human_reviews` table with before/after values
- [x] Surface correction patterns: "Intent `find_screenshot` is frequently miscategorized as `find_photo`" → suggest prompt update

**Acceptance:** 10+ human review corrections are stored; correction patterns are summarized in the evaluation page.

---

### 6.4 Automated Tests

**Tasks:**

**Backend unit tests:**
- [x] `test_connectors.py` — each connector normalizes records correctly
- [x] `test_cleaning.py` — PII detected, duplicates flagged, spam removed
- [x] `test_analysis.py` — AI analysis pipeline produces valid JSON (mock LLM responses)
- [x] `test_clustering.py` — clustering assigns clusters and labels correctly
- [x] `test_problem_discovery.py` — problems synthesized with correct scores
- [x] `test_deduplication.py` — exact and near-dedup prevents re-ingestion

**Backend integration tests:**
- [x] `test_api.py` — all endpoints return correct status codes and schema
- [x] `test_pipeline.py` — end-to-end pipeline from ingest to problem discovery (mock connectors + mock LLM)
- [x] `test_auth.py` — auth, RBAC, and token expiry work correctly
- [x] `test_phase6.py` — evaluation metrics, benchmarks, feedback loop, admin metrics, and RBAC

**Frontend tests:**
- [x] `test_overview.spec.ts` — Overview page renders KPIs
- [x] `test_problem_detail.spec.ts` — Problem detail tabs render correctly
- [x] `test_research_assistant.spec.ts` — Research query returns evidence cards

**Acceptance:** `pytest` and `npm test` both pass with ≥ 80% critical path coverage.

---

### 6.5 Observability Finalization

**Tasks:**
- [x] Verify all services emit structured JSON logs
- [x] Create `GET /admin/metrics` endpoint returning:
  - Records ingested (total + per source)
  - AI processing throughput
  - Estimated LLM token cost
  - Average analysis latency
  - Error rates
- [x] Add `/admin/metrics` page to frontend (admin role only)
- [x] Ensure every Celery job stores progress, error details, and duration in `jobs` table

**Acceptance:** Admin can view system health from within the application.

---

### 6.6 Evidence Limitations Section

**Tasks:**
- [x] Add **Evidence Limitations** panel to the Overview page:
  - Note that dataset is not statistically representative
  - Show source distribution with caveats
  - Distinguish raw volume vs. unique conversation count
  - Source bias notice (e.g., "App Store reviews skew toward negative experiences")
- [x] Add AI confidence indicators throughout — remind users that AI classifications are probabilistic

**Acceptance:** Evidence Limitations section is visible on Overview; confidence indicators appear on all AI-generated content.

---

### 6.7 Documentation

**Tasks:**
- [x] `README.md` with:
  - Project overview + architecture summary
  - Prerequisites (Docker, Node.js, Python, API keys)
  - Quick start: `docker compose up && python -m app.db.seed`
  - Environment variable reference (link to `.env.example`)
  - Running tests
  - Adding a new connector (guide)
  - Adding a new prompt version (guide)
- [x] Inline API documentation (FastAPI auto-generates OpenAPI / Swagger at `/docs`)
- [x] Code comments on all public interfaces
- [x] Update `docs/architecture.md` with any changes made during build

**Acceptance:** A developer following only `README.md` can run the app locally within 15 minutes.

---

### 6.8 Definition of Done Verification

**Walk through all 14 items from `context.md §59`:**

| # | Checkpoint | Status |
|---|---|---|
| 1 | Load/import conversation data | [x] |
| 2 | Process the data with AI | [x] |
| 3 | Search the dataset semantically | [x] |
| 4 | See identified user intents | [x] |
| 5 | See memory dimensions | [x] |
| 6 | See retrieval failure modes | [x] |
| 7 | See automatically generated problem clusters | [x] |
| 8 | Open a problem | [x] |
| 9 | Trace the problem back to evidence | [x] |
| 10 | Explore trends | [x] |
| 11 | Discover emerging problem areas | [x] |
| 12 | Ask the AI research assistant questions | [x] |
| 13 | Review/correct AI classifications | [x] |
| 14 | Generate a research brief | [x] |

**Acceptance:** All 14 checkboxes verified by a researcher doing a live walkthrough.

---

### Phase 6 Exit Criteria

- [x] Seed dataset produces meaningful insights out-of-the-box
- [x] All 14 Definition of Done items verified
- [x] `pytest` passes with ≥ 80% coverage on critical paths
- [x] README enables local setup within 15 minutes
- [x] Evidence Limitations section present in dashboard
- [x] Evaluation page shows model performance metrics
- [x] No hardcoded secrets or PII in codebase

---

## Cross-Cutting Concerns

These apply throughout **all phases**:

### Security (continuous)
- All API keys in env vars — never committed
- HTTPS enforced in any deployed environment
- Author identifiers hashed before storage
- Role guards applied to every new endpoint immediately

### Cost Management (from Phase 3)
- Dedup runs **before** any LLM call
- Stage 1 cheap model runs before Stage 2
- Cache `(conversation_id, prompt_version)` — never re-analyze same record with same prompt
- Log token usage per job

### Human-in-the-Loop (from Phase 5)
- AI output is always labeled with confidence
- Human corrections stored and feed back into evaluation
- Emerging problems require human approval before becoming permanent categories

### Evidence Traceability (from Phase 4)
- Every insight links to `evidence` rows
- Every `evidence` row links to a `conversation`
- Every `conversation` links to `source` + `url`
- Researchers can always drill down to the original text

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Source API access restricted | Medium | High | Mock connector enables full pipeline without real data; add real connectors iteratively |
| LLM cost overrun | Medium | Medium | Two-stage routing; dedup before LLM; configurable model; set token budget alerts |
| Clustering produces poor quality | Medium | Medium | Human review can merge/split/relabel clusters; tune `CLUSTER_EPSILON` in config |
| Prompt quality issues | Medium | High | Prompt versioning enables fast iteration; benchmark evaluation catches regressions |
| PII accidentally stored | Low | High | `presidio-analyzer` PII scan in cleaning pipeline; author hashing mandatory from Phase 2 |
| Embedding index performance | Low | Medium | pgvector HNSW index; upgrade to dedicated vector DB if > 1M records |

---

## Appendix — Quick-Reference Checklist

### Phase 1
- [x] Monorepo scaffold committed
- [x] Docker Compose starts all 5 services
- [x] DB schema fully migrated
- [x] Auth + RBAC working
- [x] All 6 frontend pages render
- [x] Celery processes a test task

### Phase 2
- [x] Base connector interface + mock connector working
- [x] Reddit + Play Store connectors fetch real data
- [x] Cleaning pipeline: dedup, PII, normalization
- [x] Ingestion job API working

### Phase 3
- [x] Model abstraction layer (3+ providers)
- [x] Stage 1 relevance filter job
- [x] Stage 2 deep analysis job
- [x] Embeddings stored in pgvector
- [x] Full pipeline chainable from API

### Phase 4
- [x] Semantic clustering (≥ 5 labeled clusters)
- [x] Problem discovery (≥ 5 problems with evidence)
- [x] Taxonomy assignment
- [x] Trend detection (time-series in DB)
- [x] Emerging problem detection
- [x] Unknown unknowns surfaced

### Phase 5
- [x] All 6 dashboard pages with real data
- [x] AI research assistant (RAG)
- [x] Human review workflow
- [x] Research brief generation + export
- [x] NL dataset search

### Phase 6
- [x] 100–200 record seed dataset
- [x] Evaluation framework + page
- [x] Automated tests passing
- [x] README enables 15-minute setup
- [x] All 14 Definition of Done items checked
