import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine


@pytest_asyncio.fixture(scope="function")
async def client():
    """Provides an AsyncClient for testing FastAPI endpoints with clean connection state."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    # Dispose connection pool cleanly between async test loops
    await engine.dispose()
