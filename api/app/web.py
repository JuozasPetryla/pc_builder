"""Optional frontend hosting for the single-service cloud deployment."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def mount_frontend(app: FastAPI, directory: Path | None) -> None:
    if directory is None:
        return
    if not (directory / "index.html").is_file():
        raise RuntimeError("STATIC_DIR must contain the compiled frontend index.html")
    # Register after the API. The frontend uses hash routes, so unknown paths
    # must remain 404s instead of returning index.html for misspelled API URLs.
    app.mount("/", StaticFiles(directory=directory, html=True), name="frontend")
