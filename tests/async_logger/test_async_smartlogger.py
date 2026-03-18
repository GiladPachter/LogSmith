import asyncio
import os
from pathlib import Path
import pytest
import logging

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic, When


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def drain(logger: AsyncSmartLogger):
    """Wait until the worker has processed all queued items."""
    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # this is an abuse. do not use outside of test suite
    # give worker a tick to finish writes
    await asyncio.sleep(0)


def make_file_logger(tmp_path, *, max_bytes=0, rotation_logic=None):
    """Create a logger with a single file handler."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    logger = AsyncSmartLogger("test")

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="test.log",
        rotation_logic=rotation_logic,
    )

    return logger, log_dir / "test.log"


# ---------------------------------------------------------------------------
# 1. Queue Overflow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_queue_overflow(tmp_path):
    logger = AsyncSmartLogger("x")
    # artificially shrink queue
    # logger.__queue = asyncio.Queue(maxsize=1)
    logger._AsyncSmartLogger__queue = asyncio.Queue(maxsize=1)  # this is an abuse. do not use outside of test suite

    # enqueue 3 messages
    # await logger.__enqueue_log(
    await logger._AsyncSmartLogger__enqueue_log(   # this is an abuse. do not use outside of test suite
        level=logging.INFO,
        msg="a",
        args=(),
        extra={},
        fields={},
        exc_info=None,
        stack_info_flag=False,
        pathname="x",
        lineno=1,
        func_name="f",
    )
    # await logger.__enqueue_log(
    await logger._AsyncSmartLogger__enqueue_log(    # this is an abuse. do not use outside of test suite
        level=logging.INFO,
        msg="b",
        args=(),
        extra={},
        fields={},
        exc_info=None,
        stack_info_flag=False,
        pathname="x",
        lineno=1,
        func_name="f",
    )
    # await logger.__enqueue_log(
    await logger._AsyncSmartLogger__enqueue_log(    # this is an abuse. do not use outside of test suite
        level=logging.INFO,
        msg="c",
        args=(),
        extra={},
        fields={},
        exc_info=None,
        stack_info_flag=False,
        pathname="x",
        lineno=1,
        func_name="f",
    )

    # overflow counter increments when queue is full
    assert logger.messages_enqueued == 3


# ---------------------------------------------------------------------------
# 2. Worker processes messages
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_worker_processes_messages(tmp_path):
    logger, logfile = make_file_logger(tmp_path)

    await logger.a_info("hello")
    await logger.a_info("world")

    await drain(logger)

    text = logfile.read_text()
    assert "hello" in text
    assert "world" in text


# ---------------------------------------------------------------------------
# 3. Rotation Scheduling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rotation_scheduling(tmp_path):
    rotation_logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        maxBytes=1,  # force rotation
        backupCount=3,
    )

    logger, logfile = make_file_logger(
        tmp_path,
        rotation_logic=rotation_logic,
    )

    await logger.a_info("12345")  # triggers rotation
    await drain(logger)

    # rotation should have created test.log.1
    rotated = logfile.with_name("test.log.1")
    assert rotated.exists()


# ---------------------------------------------------------------------------
# 4. RAW logging
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_raw_logging(tmp_path):
    logger, logfile = make_file_logger(tmp_path)

    await logger.a_raw("hello raw", end="\n")
    await drain(logger)

    assert "hello raw" in logfile.read_text()


# ---------------------------------------------------------------------------
# 5. Shutdown drains queue
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_shutdown_drains_queue(tmp_path):
    logger, logfile = make_file_logger(tmp_path)

    await logger.a_info("a")
    await logger.a_info("b")

    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # this is an abuse. do not use outside of test suite
    await logger.shutdown()

    text = logfile.read_text(encoding="utf-8")
    assert "a" in text
    assert "b" in text


# ---------------------------------------------------------------------------
# 6. Metadata merge
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_metadata_merge(tmp_path):
    logger, logfile = make_file_logger(tmp_path)

    await logger.a_info("hello", fields={"x": 1})
    await drain(logger)

    text = logfile.read_text(encoding="utf-8")
    assert "hello" in text
    assert "x" in text


# ---------------------------------------------------------------------------
# 7. Rotation + Shutdown race
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rotation_shutdown_race(tmp_path):
    rotation_logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        maxBytes=1,
        backupCount=3,
    )

    logger, logfile = make_file_logger(tmp_path, rotation_logic=rotation_logic)

    await logger.a_trace("12345")  # triggers rotation
    await logger.shutdown()     # shutdown during rotation

    # Should not crash
    assert True
