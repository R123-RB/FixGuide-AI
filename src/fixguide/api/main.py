"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from fixguide.api.deps import get_graph
from fixguide.api.middleware import LoggingMiddleware
from fixguide.api.routes import health, repair
from fixguide.config import get_settings
from fixguide.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize logging and the LangGraph graph on startup."""
    setup_logging()
    get_graph()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(repair.router, prefix="/api/v1/repair", tags=["repair"])

# Serve static frontend
STATIC_DIR = Path(__file__).resolve().parent.parent.parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_model=None)
async def root() -> FileResponse | dict[str, str]:
    """Serve the frontend."""
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"name": settings.app_name, "version": settings.app_version}
