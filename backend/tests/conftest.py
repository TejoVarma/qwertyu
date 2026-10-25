import socket
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine

# Resilient DNS resolution fallback for Neon Serverless AWS Singapore endpoint
_orig_getaddrinfo = socket.getaddrinfo
def _resilient_getaddrinfo(host, port, *args, **kwargs):
    if isinstance(host, str) and "neon.tech" in host:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("13.251.213.89", port or 5432))]
    return _orig_getaddrinfo(host, port, *args, **kwargs)

socket.getaddrinfo = _resilient_getaddrinfo


@pytest_asyncio.fixture(scope="function")
async def client():
    """Provides an AsyncClient for testing FastAPI endpoints with clean connection state."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    # Dispose connection pool cleanly between async test loops
    await engine.dispose()
