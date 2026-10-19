"""CLI entry point."""

from __future__ import annotations

import typer

from fixguide.pipelines import evaluate, fine_tune, ingest

app = typer.Typer()
app.add_typer(ingest.app, name="ingest")
app.add_typer(evaluate.app, name="eval")
app.add_typer(fine_tune.app, name="fine-tune")


@app.command()
def serve() -> None:
    """Start API server."""
    import uvicorn

    from fixguide.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "fixguide.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.env == "development",
    )


if __name__ == "__main__":
    app()
