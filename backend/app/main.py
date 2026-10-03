from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db.session import engine
from app.db import models as db_models
from app.api.routes import (
    auth,
    health,
    jobs,
    conversations,
    problems,
    clusters,
    trends,
    evidence,
    reviews,
    research,
    reports,
    ingest,
    pipeline,
    taxonomy,
    stats,
)
from app.db.seed import seed_admin_user, seed_sources, seed_prompts

# ── Structured logger ──────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()
settings = get_settings()


# ── Lifespan ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", env=settings.app_env, ai_provider=settings.ai_provider)
    # Create tables (Alembic handles migrations; this is a safety net for tests)
    async with engine.begin() as conn:
        pass  # Tables managed via alembic; don't auto-create here
    # Seed admin user on every startup (idempotent)
    await seed_admin_user()
    # Seed connector sources (idempotent)
    await seed_sources()
    # Seed prompt versions (idempotent)
    await seed_prompts()
    yield
    log.info("shutdown")


# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Photo Discovery Engine",
    description="AI-powered photo retrieval research platform",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request ID + structured logging middleware ─────────────────────────────
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)
    log.info(
        "http_request",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response


# ── Exception handler ─────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from fastapi import HTTPException
    from starlette.exceptions import HTTPException as StarletteHTTPException
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    log.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
app.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
app.include_router(problems.router, prefix="/problems", tags=["Problems"])
app.include_router(clusters.router, prefix="/clusters", tags=["Clusters"])
app.include_router(trends.router, prefix="/trends", tags=["Trends"])
app.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])
app.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
app.include_router(research.router, prefix="/research", tags=["Research"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])
app.include_router(pipeline.router, prefix="/pipeline", tags=["Pipeline"])
app.include_router(taxonomy.router, prefix="/taxonomy", tags=["Taxonomy"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])
