import asyncio
import logging

import pytest

from LogSmith import RotationLogic
from LogSmith.async_smartlogger import AsyncSmartLogger


class BoomQueueFull:
    """Simulates a queue whose put_nowait always raises QueueFull."""
    def __init__(self):
        self.calls = 0

    def boom(self, *args, **kwargs):
        self.calls += 1
        raise asyncio.QueueFull


@pytest.mark.asyncio
async def test_enqueue_log_exponential_backoff(monkeypatch):
    lg = AsyncSmartLogger("backpressure_log")

    # Install boom() on put_nowait
    boom = BoomQueueFull()
    monkeypatch.setattr(
        lg._AsyncSmartLogger__queue,
        "put_nowait",
        boom.boom
    )

    # Should NOT raise
    await lg.a_info("hello")

    # Should have attempted multiple retries
    assert boom.calls >= 3


@pytest.mark.asyncio
async def test_enqueue_raw_exponential_backoff(monkeypatch):
    lg = AsyncSmartLogger("backpressure_raw")

    boom = BoomQueueFull()
    monkeypatch.setattr(
        lg._AsyncSmartLogger__queue,
        "put_nowait",
        boom.boom
    )

    # Should NOT raise
    await lg.a_raw(logging.INFO, "hello")

    # Should have attempted multiple retries
    assert boom.calls >= 3


@pytest.mark.asyncio
async def test_enqueue_log_drops_after_max_retries(monkeypatch):
    lg = AsyncSmartLogger("drop_log")

    class AlwaysFull:
        def __init__(self):
            self.calls = 0
        def boom(self, *a, **kw):
            self.calls += 1
            raise asyncio.QueueFull

    full = AlwaysFull()

    # Force put_nowait to ALWAYS fail
    monkeypatch.setattr(
        lg._AsyncSmartLogger__queue,
        "put_nowait",
        full.boom
    )

    # Should NOT raise
    await lg.a_info("hello")

    # Should have attempted all retries
    assert full.calls >= 5


@pytest.mark.asyncio
async def test_enqueue_raw_drops_after_max_retries(monkeypatch):
    lg = AsyncSmartLogger("drop_raw")

    class AlwaysFull:
        def __init__(self):
            self.calls = 0
        def boom(self, *a, **kw):
            self.calls += 1
            raise asyncio.QueueFull

    full = AlwaysFull()

    monkeypatch.setattr(
        lg._AsyncSmartLogger__queue,
        "put_nowait",
        full.boom
    )

    # Should NOT raise
    await lg.a_raw(logging.INFO, "hello")

    # Should have attempted all retries
    assert full.calls >= 5


@pytest.mark.asyncio
async def test_rotation_callback_survives_queuefull(tmp_path, monkeypatch):
    lg = AsyncSmartLogger("rotate_queuefull")

    logic = RotationLogic(maxBytes=10, backupCount=1)
    lg.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]

    class AlwaysFull:
        def __init__(self):
            self.calls = 0
        def boom(self, *a, **kw):
            self.calls += 1
            raise asyncio.QueueFull

    full = AlwaysFull()

    monkeypatch.setattr(
        lg._AsyncSmartLogger__queue,
        "put_nowait",
        full.boom
    )

    # Should NOT raise
    handler.rotation_callback(handler)

    # Allow scheduled task to run
    await asyncio.sleep(0.01)

    # Should have attempted retries
    assert full.calls >= 3


@pytest.mark.asyncio
async def test_audit_forwarding_survives_queuefull(tmp_path, monkeypatch):
    # Enable auditing
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    audit_logger = AsyncSmartLogger._AsyncSmartLogger__audit_logger

    class AlwaysFull:
        def __init__(self):
            self.calls = 0
        def boom(self, *a, **kw):
            self.calls += 1
            raise asyncio.QueueFull

    full = AlwaysFull()

    # Patch audit logger queue
    monkeypatch.setattr(
        audit_logger._AsyncSmartLogger__queue,
        "put_nowait",
        full.boom
    )

    lg = AsyncSmartLogger("src_logger")

    # Should NOT raise even though audit forwarding fails internally
    await lg.a_info("hello")
    await lg.flush()

    # Allow scheduled tasks to run
    await asyncio.sleep(0.01)

    # Should have attempted retries
    assert full.calls >= 3

    await AsyncSmartLogger.terminate_auditing()
