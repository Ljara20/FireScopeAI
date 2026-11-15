"""Tests for API dependency injection."""

from pathlib import Path

import duckdb
import pytest

from firescope.infrastructure.persistence.duckdb_repository import (
    DuckDbRepository,
)
from firescope.presentation.api import dependencies


def test_get_project_root() -> None:
    root = dependencies.get_project_root()

    assert (root / "data").is_dir()
    assert (root / "backend").is_dir()


def test_get_repository(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    project_root = tmp_path
    (project_root / "data").mkdir()

    monkeypatch.setattr(
        dependencies,
        "get_project_root",
        lambda: project_root,
    )

    generator = dependencies.get_repository()
    repository = next(generator)

    try:
        assert isinstance(repository, DuckDbRepository)
        assert repository.data_dir == (project_root / "data").resolve()
    finally:
        generator.close()


def test_repository_connection_closes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "data").mkdir()

    monkeypatch.setattr(
        dependencies,
        "get_project_root",
        lambda: tmp_path,
    )

    generator = dependencies.get_repository()
    repository = next(generator)

    assert repository.connection.execute("SELECT 1").fetchone() == (1,)

    generator.close()

    with pytest.raises(duckdb.ConnectionException):
        repository.connection.execute("SELECT 1")
