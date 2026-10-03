# Deployment Guide — Photo Discovery Engine

This guide walks you through deploying the **Photo Discovery Engine** to production using **Vercel** for the frontend, alongside managed backend services.

---

## 1. Architectural Overview for Deployment

| Layer | Recommended Host | Why |
|---|---|---|
| **Frontend** | **Vercel** | Next.js 14/16 App Router, edge CDN, zero-config SSR & prerendering. |
| **Backend API** | **Railway** or **Render** | Runs FastAPI container with persistent networking and healthchecks. |
| **Worker & Beat** | **Railway** or **Render** | Long-running Celery worker and scheduler for scraping & clustering. |
| **Database** | **Supabase** or **Neon** | PostgreSQL 16 with native `pgvector` HNSW extension. |
| **Cache & Queue** | **Upstash** or **Redis Cloud** | Serverless / managed Redis 7 broker. |

> **Important Note Regarding Vercel:**  
> Vercel is a **serverless platform** designed for frontends and stateless HTTP functions. It **cannot** run persistent Celery background workers or host a PostgreSQL `pgvector` database. Therefore, the standard industry practice is **Frontend on Vercel + Backend & Workers on Railway / Render + Database on Supabase / Neon**.

---

## 2. Deploying the Frontend to Vercel

### Step 1: Import Project into Vercel
1. Log in to [vercel.com](https://vercel.com) and click **"Add New Project"**.
2. Select your Git repository: `Photo Discovery Engine`.
3. In the configuration screen, expand **"Root Directory"** and click **Edit**.
4. Select `frontend` as the **Root Directory** (or keep root if using `vercel.json`).
5. Vercel will automatically detect **Framework Preset: Next.js**.

### Step 2: Configure Environment Variables in Vercel
In the Vercel project settings, add the following 3 Environment Variables under **Settings > Environment Variables**:

| Variable | Value / Description | Example |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Public HTTPS URL where your FastAPI backend is running | `https://api.yourdomain.com` or `https://photo-engine-backend.up.railway.app` |
| `NEXTAUTH_URL` | Canonical URL of your Vercel deployment | `https://your-photo-discovery-app.vercel.app` |
| `NEXTAUTH_SECRET` | A secure 32+ character secret for JWT signing | Generate via `openssl rand -hex 32` |

### Step 3: Deploy
Click **Deploy**. Vercel will build all 11 static and dynamic routes. When build completes, your frontend will be live on `https://your-photo-discovery-app.vercel.app`.

---

## 3. Deploying Backend, Database & Workers

### Option A: Railway (Fastest & Simplest)
1. In [Railway.app](https://railway.app), create a **New Project**.
2. **Add PostgreSQL:** Add a Postgres database with pgvector (`CREATE EXTENSION IF NOT EXISTS vector;`).
3. **Add Redis:** Add a managed Redis service.
4. **Deploy Backend Service:**
   - Source: Same Git repository.
   - Root Directory: `backend`
   - Build command: uses `backend/Dockerfile`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Deploy Celery Worker Service:**
   - Same repo & Dockerfile.
   - Start command: `celery -A app.worker.celery_app worker --loglevel=info --concurrency=4`
6. **Set Environment Variables on Railway:**
   - `DATABASE_URL`: `${{Postgres.DATABASE_URL}}`
   - `REDIS_URL`: `${{Redis.REDIS_URL}}`
   - `JWT_SECRET`: Random 32+ character string
   - `ADMIN_PASSWORD`: Your chosen admin password
   - `AI_PROVIDER`: `groq`
   - `GROQ_API_KEY`: `gsk_...`
   - `OPENAI_API_KEY`: `sk-...`
   - `APIFY_API_TOKEN`: `apify_api_...`
   - `YOUTUBE_API_KEY`: `AIzaSy...`
   - `CORS_ORIGINS`: `https://your-photo-discovery-app.vercel.app`

### Option B: Render.com
1. Create a **Managed PostgreSQL** on Render (supports pgvector).
2. Create a **Redis instance** on Render.
3. Create a **Web Service** for `backend` pointing to the repo root with Dockerfile `backend/Dockerfile`.
4. Create a **Background Worker** for Celery with command `celery -A app.worker.celery_app worker --loglevel=info`.

### Option C: Single Cloud VM (AWS EC2 / DigitalOcean Droplet / Hetzner)
You can deploy the entire stack using the included `docker-compose.yml`:
```bash
git clone <repo-url>
cd "Photo Discovery Engine"
cp .env.example .env
# Edit .env with your production secrets
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.db.seed
```

---

## 4. Post-Deployment Verification Checklist

1. [ ] **Backend Health Check:** Visit `https://api.yourdomain.com/health` (should return `{"status":"ok"}`).
2. [ ] **Swagger API Docs:** Visit `https://api.yourdomain.com/docs`.
3. [ ] **Database Seed:** Run `python -m app.db.seed` to seed 125 conversations and benchmarks.
4. [ ] **Frontend Login:** Open your Vercel URL, log in with `admin@example.com` and your configured password.
5. [ ] **Overview Page:** Verify KPI cards and charts load data from the backend.
6. [ ] **CORS Verification:** Ensure browser requests to `NEXT_PUBLIC_API_URL` succeed without CORS headers errors (handled via backend regex `^https://.*\.vercel\.app$`).
