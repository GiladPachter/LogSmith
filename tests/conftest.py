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


import pytest
import logging
import uuid
import asyncio
from LogSmith.async_smartlogger import AsyncSmartLogger

@pytest.fixture
async def clean_async_logger():
    """
    Provides a fully isolated AsyncSmartLogger instance.

    - Runs inside pytest-asyncio's event loop
    - Ensures unique logger name per test
    - Clears class-level global state
    - Removes handlers from the underlying logging.Logger
    - Shuts down worker tasks cleanly after the test
    """

    # 1. Reset class-level global state
    AsyncSmartLogger._AsyncSmartLogger__audit_enabled = False
    AsyncSmartLogger._AsyncSmartLogger__audit_logger = None
    AsyncSmartLogger._AsyncSmartLogger__audit_handler = None
    AsyncSmartLogger._AsyncSmartLogger__messages_processed = 0

    # 2. Unique logger name (prevents handler reuse)
    unique_name = f"test_logger_{uuid.uuid4().hex}"
    py_logger = logging.getLogger(unique_name)

    # 3. Remove any pre-existing handlers
    for h in list(py_logger.handlers):
        py_logger.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass

    # 4. Create the AsyncSmartLogger inside the running event loop
    logger = AsyncSmartLogger(unique_name)

    yield logger

    # 5. Clean shutdown of worker tasks
    logger._stopped = True

    # Send sentinel to each worker
    for _ in getattr(logger, "_worker_tasks", []):
        await logger._queue.put(
            logger._QueueItem(op=logger.AsyncOp.SENTINEL, payload={})
        )

    # Wait for workers to exit
    for task in getattr(logger, "_worker_tasks", []):
        try:
            await task
        except Exception:
            pass

    # 6. Remove handlers from underlying logging.Logger
    for h in list(py_logger.handlers):
        py_logger.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass
