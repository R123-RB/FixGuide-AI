"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from fixguide.config import get_settings
from fixguide.models.api import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Report service and dependency health."""
    settings = get_settings()
    return HealthResponse(status="healthy", version=settings.app_version)
