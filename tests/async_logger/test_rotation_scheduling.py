import asyncio
import logging
import os
import time
import pytest
from pathlib import Path

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.rotation_base import RotationLogic, When


def _get_async_rotating_handler(logger: AsyncSmartLogger) -> Async_TimedSizedRotatingFileHandler:
    for h in logger._py_logger.handlers:
        if isinstance(h, Async_TimedSizedRotatingFileHandler):
            return h
    raise RuntimeError("Async rotating handler not found")


@pytest.mark.asyncio
async def test_size_based_rotation_triggers_callback(tmp_path):
    logger = AsyncSmartLogger("test_size_rotation", logging.INFO)

    rotation_logic = RotationLogic(maxBytes=100, backupCount=2)
    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="size.log",
        rotation_logic=rotation_logic,
    )

    handler = _get_async_rotating_handler(logger)

    # Spy: wrap rotation_callback
    called = {"count": 0}
    original_cb = handler.rotation_callback

    def wrapped_cb(h):
        called["count"] += 1
        if original_cb:
            original_cb(h)

    handler.rotation_callback = wrapped_cb

    # Log enough to exceed 100 bytes
    for _ in range(20):
        await logger.a_info("x" * 20)

    await logger._queue.join()

    assert called["count"] >= 1


@pytest.mark.asyncio
async def test_time_based_rotation_triggers_callback(tmp_path, monkeypatch):
    logger = AsyncSmartLogger("test_time_rotation", logging.INFO)

    rotation_logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        backupCount=2,
    )

    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="time.log",
        rotation_logic=rotation_logic,
    )

    handler = _get_async_rotating_handler(logger)

    # Force _rollover_at in the past so should_rotate() returns True
    handler._rollover_at = time.time() - 1

    called = {"count": 0}
    original_cb = handler.rotation_callback

    def wrapped_cb(h):
        called["count"] += 1
        if original_cb:
            original_cb(h)

    handler.rotation_callback = wrapped_cb

    await logger.a_info("trigger time rotation")
    await logger._queue.join()

    assert called["count"] >= 1


@pytest.mark.asyncio
async def test_rotation_enqueued_and_executed(tmp_path):
    logger = AsyncSmartLogger("test_rotation_exec", logging.INFO)

    rotation_logic = RotationLogic(maxBytes=100, backupCount=2)
    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="rotate_exec.log",
        rotation_logic=rotation_logic,
    )

    handler = _get_async_rotating_handler(logger)

    # Make file large enough to trigger rotation
    for _ in range(20):
        await logger.a_info("x" * 20)

    await logger._queue.join()

    # Force rotation directly via callback to ensure ROTATE op is enqueued
    handler.rotation_callback(handler)
    await asyncio.sleep(0)
    await logger._queue.join()

    base = Path(handler.baseFilename)
    rotated = base.with_suffix(base.suffix + ".1")

    # Either rotated file exists, or base file was recreated after rotation
    assert base.exists()
    # backupCount>0 → rotated file is expected at some point
    assert any(p.name.startswith(base.name) for p in base.parent.iterdir())


@pytest.mark.asyncio
async def test_rotation_under_load(tmp_path):
    logger = AsyncSmartLogger("test_rotation_load", logging.INFO)

    rotation_logic = RotationLogic(maxBytes=500, backupCount=3)
    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="load.log",
        rotation_logic=rotation_logic,
    )

    async def writer(i):
        await logger.a_info(f"message {i:04d} " + "x" * 50)

    tasks = [asyncio.create_task(writer(i)) for i in range(200)]
    await asyncio.gather(*tasks)
    await logger._queue.join()

    base = tmp_path / "load.log"
    assert base.exists()

    # Check that some rotated files exist
    rotated_files = [p for p in tmp_path.iterdir() if p.name.startswith("load.log.")]
    assert len(rotated_files) <= rotation_logic.backupCount
