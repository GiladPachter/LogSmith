# Auto-generated pytest fixtures for LogSmith

import asyncio
import json
import logging
import sys
import time
import uuid

import pytest

from pathlib import Path

from LogSmith import SmartLogger
from LogSmith import AsyncSmartLogger
from LogSmith.level_registry import reset_levels_for_tests


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


levels = SmartLogger.levels()


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


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


@pytest.fixture(autouse=True)
def reset_level_registry():
    reset_levels_for_tests()


@pytest.fixture
def tmp_log_dir(tmp_path):
    d = tmp_path / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


# import uuid
# import pytest
# from LogSmith.smartlogger import SmartLogger
# from LogSmith.levels import TRACE

@pytest.fixture
def logger():
    name = f"test_smartlogger_{uuid.uuid4().hex}"
    lg = SmartLogger(name, levels["TRACE"])
    try:
        yield lg
    finally:
        # optional: destroy/retire to clean up handlers
        # noinspection PyProtectedMember
        for h in list(lg._py_logger.handlers):
            # noinspection PyProtectedMember
            lg._py_logger.removeHandler(h)
            h.close()


@pytest.fixture
def flush():
    def _flush():
        time.sleep(0.01)
    return _flush


@pytest.fixture
async def async_logger():
    name = f"test_async_logger_{uuid.uuid4().hex}"
    logger = AsyncSmartLogger(name, levels["TRACE"])
    try:
        yield logger
    finally:
        await logger.shutdown()


@pytest.fixture
async def clean_async_logger():
    """
    Provides a fully isolated AsyncSmartLogger instance without trying to
    manually shut down worker tasks (which AsyncSmartLogger does not support).
    """

    # Reset class-level global state
    AsyncSmartLogger._AsyncSmartLogger__audit_enabled = False
    AsyncSmartLogger._AsyncSmartLogger__audit_logger = None
    AsyncSmartLogger._AsyncSmartLogger__audit_handler = None
    AsyncSmartLogger._AsyncSmartLogger__messages_processed = 0

    # Unique logger name
    unique_name = f"test_logger_{uuid.uuid4().hex}"
    py_logger = logging.getLogger(unique_name)

    # Remove any existing handlers
    for h in list(py_logger.handlers):
        py_logger.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass

    # Create logger inside running event loop
    logger = AsyncSmartLogger(unique_name)

    yield logger

    # Cleanup: remove handlers (do NOT try to stop worker tasks)
    for h in list(py_logger.handlers):
        py_logger.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass
