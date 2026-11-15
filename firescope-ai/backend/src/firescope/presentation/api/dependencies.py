"""Dependency injection for the FireScope AI API."""

from collections.abc import Iterator
from pathlib import Path

from firescope.infrastructure.persistence.duckdb_repository import (
    DuckDbRepository,
)
from firescope.shared.config import Settings


def get_project_root() -> Path:
    """Locate the FireScope AI project directory."""
    current = Path(__file__).resolve()

    for parent in current.parents:
        if (parent / "data").is_dir() and (parent / "backend").is_dir():
            return parent

    raise RuntimeError("FireScope AI project root not found")


def get_repository() -> Iterator[DuckDbRepository]:
    """Provide a DuckDB repository and close it after the request."""
    settings = Settings.from_project(get_project_root())
    repository = DuckDbRepository(settings.data_dir)

    try:
        yield repository
    finally:
        repository.close()
