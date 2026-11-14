"""Integration tests for API."""

import pytest
from httpx import ASGITransport, AsyncClient

from fixguide.api.main import app


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """Verify /health/ returns 200 and healthy status."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint() -> None:
    """Verify root endpoint returns HTML frontend or JSON fallback."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        # Root serves HTML frontend or JSON fallback
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type:
            assert "FixGuide" in response.text or "fixguide" in response.text.lower()
        else:
            assert "name" in response.json()
