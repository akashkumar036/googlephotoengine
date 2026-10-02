from fastapi import APIRouter
from app.db.session import engine

router = APIRouter()


@router.get("/health", summary="Health check")
async def health():
    """Returns 200 OK when the service is running."""
    return {"status": "ok", "service": "photo-discovery-engine"}


@router.get("/health/db", summary="DB health check")
async def health_db():
    """Verifies a DB connection can be acquired."""
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}
