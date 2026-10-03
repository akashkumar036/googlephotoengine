import os
import sys
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Ensure backend root is on sys.path
_backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

# Hermetic test environment defaults
os.environ["AI_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"

from app.main import app
from app.db.models import Base, User, _uuid
from app.db.session import get_db
from app.auth.security import hash_password, create_access_token
from app.worker.celery_app import celery_app

celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True


ADMIN_USER_ID = "00000000-0000-0000-0000-000000000001"
RESEARCHER_USER_ID = "00000000-0000-0000-0000-000000000002"
VIEWER_USER_ID = "00000000-0000-0000-0000-000000000003"


@pytest_asyncio.fixture
async def test_db_session():
    """Create a fresh in-memory SQLite database and yield an AsyncSession."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        session.add(User(
            id=ADMIN_USER_ID,
            email="admin@example.com",
            role="admin",
            hashed_password=hash_password("adminpass123"),
        ))
        session.add(User(
            id=RESEARCHER_USER_ID,
            email="researcher@example.com",
            role="researcher",
            hashed_password=hash_password("researchpass123"),
        ))
        session.add(User(
            id=VIEWER_USER_ID,
            email="viewer@example.com",
            role="viewer",
            hashed_password=hash_password("viewerpass123"),
        ))
        await session.commit()

    async def override_get_db():
        async with Session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    import app.db.session as db_session_module
    import app.pipeline.orchestrator as orch_module
    import app.worker.tasks as task_module
    import app.pipeline.ingestion as ing_module

    orig_db_asl = db_session_module.AsyncSessionLocal
    orig_orch_asl = getattr(orch_module, "AsyncSessionLocal", None)
    orig_task_asl = getattr(task_module, "AsyncSessionLocal", None)

    db_session_module.AsyncSessionLocal = Session
    orch_module.AsyncSessionLocal = Session
    task_module.AsyncSessionLocal = Session

    try:
        async with Session() as session:
            yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        db_session_module.AsyncSessionLocal = orig_db_asl
        if orig_orch_asl:
            orch_module.AsyncSessionLocal = orig_orch_asl
        if orig_task_asl:
            task_module.AsyncSessionLocal = orig_task_asl
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db_session):
    """Alias fixture for test_db_session."""
    return test_db_session


@pytest_asyncio.fixture
async def client(test_db_session):
    """Async test client with test DB session injected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def admin_headers():
    token = create_access_token(user_id=ADMIN_USER_ID, role="admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def researcher_headers():
    token = create_access_token(user_id=RESEARCHER_USER_ID, role="researcher")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_headers():
    token = create_access_token(user_id=VIEWER_USER_ID, role="viewer")
    return {"Authorization": f"Bearer {token}"}
