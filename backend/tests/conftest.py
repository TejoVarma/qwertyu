import os

# API tests run against a dedicated, seeded test database, never the deployed one.
# Default: the docker-compose Postgres (localhost:5433). Override with TEST_DATABASE_URL.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://energy_trader:energy_secure_pwd_2026@localhost:5433/wind_procure_iq_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import asyncpg  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import AsyncClient, ASGITransport  # noqa: E402
from app.main import app  # noqa: E402
from app.core.database import engine, init_db  # noqa: E402
from tests.seed import seed_test_data  # noqa: E402


async def _ensure_database_exists() -> None:
    url = TEST_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    server_url, db_name = url.rsplit("/", 1)
    conn = await asyncpg.connect(f"{server_url}/postgres")
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="function")
async def client():
    """AsyncClient over the FastAPI app, backed by a freshly seeded test database."""
    try:
        await _ensure_database_exists()
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(f"Test database unavailable ({exc}). Start it with: docker compose up -d postgres")

    await init_db()
    await seed_test_data(engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await engine.dispose()
