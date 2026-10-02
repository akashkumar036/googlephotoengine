# Photo Discovery Engine

An AI-powered **Photo Retrieval Discovery Engine** — a research and product-discovery system that continuously analyzes publicly available user conversations to discover, understand, and prioritize problems people face when trying to retrieve old, forgotten, or difficult-to-find photos and videos.

## Docs

- [`docs/context.md`](docs/context.md) — Project context and requirements summary
- [`docs/architecture.md`](docs/architecture.md) — System architecture
- [`docs/implementation-plan.md`](docs/implementation-plan.md) — Phase-wise implementation plan
- [`docs/edge-cases.md`](docs/edge-cases.md) — Edge cases and corner scenarios

## Quick Start (Local Development)

### Prerequisites

| Tool | Minimum Version |
|---|---|
| Docker Desktop | 4.x |
| Docker Compose | v2.x |
| Node.js | 20 LTS |
| Python | 3.11+ |

### 1. Clone and configure environment

```bash
git clone <repo-url>
cd photo-discovery-engine
cp .env.example .env
# Edit .env and fill in required values (API keys, secrets)
```

### 2. Start all services

```bash
docker compose up --build
```

This starts:
- **PostgreSQL + pgvector** on port `5432`
- **Redis** on port `6379`
- **Backend API** on port `8000` — http://localhost:8000
- **Celery Worker** (background jobs)
- **Frontend** on port `3000` — http://localhost:3000

### 3. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Seed demo data (optional)

```bash
docker compose exec backend python -m app.db.seed
```

### 5. Access the app

| Service | URL |
|---|---|
| Frontend Dashboard | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

Default admin credentials (set in `.env`):
- **Email:** `admin@example.com`
- **Password:** from `ADMIN_PASSWORD` in `.env`

## Running Tests

```bash
# Backend
docker compose exec backend pytest --cov=app tests/

# Frontend
cd frontend && npm test
```

## Project Structure

```
photo-discovery-engine/
├── backend/                — Python / FastAPI backend
│   ├── app/
│   │   ├── api/            — Route handlers
│   │   ├── connectors/     — Source-specific data connectors
│   │   ├── pipeline/       — AI analysis pipeline stages
│   │   ├── models/         — LLM provider abstraction
│   │   ├── db/             — ORM models and migrations
│   │   └── worker/         — Celery tasks
│   └── tests/
├── frontend/               — Next.js 14 dashboard
│   └── app/                — App Router pages
├── docs/                   — Project documentation
├── docker-compose.yml
└── .env.example
```

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full system architecture.

**Stack summary:**
- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Alembic
- **LLM:** Groq (primary — OpenAI-compatible API, ultra-low latency)
- **Embeddings:** OpenAI `text-embedding-3-small`
- **Database:** PostgreSQL 16 + pgvector
- **Jobs:** Celery + Redis
