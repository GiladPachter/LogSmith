# Auto-generated pytest fixtures for LogSmith

import asyncio
import importlib
import json
import logging
from pathlib import Path


import pytest
import LogSmith
import LogSmith.level_registry
import LogSmith.smartlogger


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def temp_logs_dir(tmp_path: Path) -> Path:
    d = tmp_path / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def temp_audit_dir(tmp_path: Path) -> Path:
    d = tmp_path / "audit"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def ndjson_loader():
    def _load(path: Path):
        records = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return records
    return _load


@pytest.fixture
def force_rotation():
    def _force(handler, *, size_bytes: int | None = None):
        if size_bytes is not None:
            handler.baseFilename and Path(handler.baseFilename).write_text("x" * size_bytes)
        if hasattr(handler, "doRollover"):
            handler.doRollover()
    return _force


from LogSmith.level_registry import reset_levels_for_tests

@pytest.fixture(autouse=True)
def reset_level_registry():
    reset_levels_for_tests()
