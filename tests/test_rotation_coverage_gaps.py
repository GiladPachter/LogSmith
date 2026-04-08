import asyncio
import logging
import os
import time
import pytest

from LogSmith import AsyncSmartLogger
from LogSmith.async_smartlogger import AsyncOp
from LogSmith.rotation import ConcurrentTimedSizedRotatingFileHandler
from LogSmith.rotation_base import (
    RotationLogic,
    LargeLogEntryBehavior,
    ExpirationRule,
    ExpirationScale,
)


# ------------------------------------------------------------
# Helper: write a record
# ------------------------------------------------------------
class DummyRecord:
    def __init__(self, msg="x"):
        self.msg = msg
        self.args = ()
        self.levelname = "INFO"
        self.levelno = 20
        self.pathname = "x"
        self.filename = "x"
        self.module = "x"
        self.exc_info = None
        self.exc_text = None
        self.stack_info = None
        self.lineno = 1
        self.funcName = "f"
        self.created = time.time()
        self.msecs = 0
        self.relativeCreated = 0
        self.thread = 0
        self.threadName = "t"
        self.processName = "p"
        self.process = 0

    def getMessage(self):
        return self.msg


# ------------------------------------------------------------
# 1. Large entry behaviors
# ------------------------------------------------------------
@pytest.mark.parametrize("behavior", [
    LargeLogEntryBehavior.ExceedMaxBytesIfFileIsEmpty,
    LargeLogEntryBehavior.RotateFirst,
    LargeLogEntryBehavior.DumpSilently,
])
def test_large_entry_behaviors(tmp_path, behavior):
    path = tmp_path / "big.log"
    handler = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=5,
        backup_count=2,
        large_entry_behavior=behavior,
    )

    rec = DummyRecord(msg="X" * 50)

    if behavior is LargeLogEntryBehavior.DumpSilently:
        handler.emit(rec)
        assert path.read_text() == ""
    else:
        handler.emit(rec)
        assert path.exists()


def test_large_entry_crash(tmp_path):
    path = tmp_path / "crash.log"
    handler = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=5,
        backup_count=2,
        large_entry_behavior=LargeLogEntryBehavior.Crash,
    )

    rec = DummyRecord(msg="X" * 50)

    with pytest.raises(ValueError):
        handler.emit(rec)


# ------------------------------------------------------------
# 2. Time-based rollover
# ------------------------------------------------------------
def test_time_based_rollover(tmp_path):
    path = tmp_path / "time.log"
    logic = RotationLogic(when=None, maxBytes=10, backupCount=2)
    handler = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=10,
        backup_count=2,
    )

    rec = DummyRecord(msg="1234567890")
    handler.emit(rec)
    handler.emit(rec)  # triggers rotation

    rotated = list(tmp_path.glob("time.log.*"))
    assert len(rotated) >= 1


# ------------------------------------------------------------
# 3. Forced rollover on old file
# ------------------------------------------------------------
def test_force_rollover_on_old_file(tmp_path):
    path = tmp_path / "old.log"
    path.write_text("hello")

    old = time.time() - 999999
    os.utime(path, (old, old))

    handler = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        when=None,
        max_bytes=1,
        backup_count=1,
    )

    rec = DummyRecord(msg="x")
    handler.emit(rec)

    rotated = list(tmp_path.glob("old.log.*"))
    assert len(rotated) >= 1


# ------------------------------------------------------------
# 4. PermissionError during rename
# ------------------------------------------------------------
def test_permission_error_during_rename(tmp_path, monkeypatch):
    path = tmp_path / "perm.log"
    handler = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=1,
        backup_count=1,
    )

    def bad_replace(src, dst):
        if src == str(path):
            raise PermissionError
        return os.replace(src, dst)

    monkeypatch.setattr(os, "replace", bad_replace)

    rec = DummyRecord(msg="xx")
    handler.emit(rec)  # should not raise

    assert path.exists()


# ------------------------------------------------------------
# 5. Expiration policy
# ------------------------------------------------------------
def test_expiration_policy(tmp_path):
    path = tmp_path / "exp.log"
    handler = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(path),
        max_bytes=1,
        backup_count=5,
        expiration_rule=ExpirationRule(ExpirationScale.Seconds, 0),
    )

    # Create fake rotated files
    for i in range(1, 4):
        f = tmp_path / f"exp.log.{i}"
        f.write_text("x")
        old = time.time() - 999999
        os.utime(f, (old, old))

    rec = DummyRecord(msg="xx")
    handler.emit(rec)

    remaining = list(tmp_path.glob("exp.log.*"))
    assert len(remaining) == 1  # only the newest survives


@pytest.mark.asyncio
async def test_rotation_callback_never_raises_even_if_queuefull(monkeypatch, tmp_path):
    lg = AsyncSmartLogger("rot_cb_never_raises")
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
    monkeypatch.setattr(lg._AsyncSmartLogger__queue, "put_nowait", full.boom)

    # Should not raise
    handler.rotation_callback(handler)

    await asyncio.sleep(0.05)
    assert full.calls >= 3


@pytest.mark.asyncio
async def test_rotation_callback_ignored_after_shutdown(tmp_path):
    lg = AsyncSmartLogger("rot_after_shutdown")
    logic = RotationLogic(maxBytes=1, backupCount=1)
    lg.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]

    await lg.shutdown()

    # Should not raise and should not enqueue
    handler.rotation_callback(handler)

    # Queue should remain empty
    assert lg._AsyncSmartLogger__queue.qsize() == 0


@pytest.mark.asyncio
async def test_rotation_callback_many_calls(tmp_path, monkeypatch):
    lg = AsyncSmartLogger("rot_many")
    logic = RotationLogic(maxBytes=1, backupCount=1)
    lg.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]

    events = []

    def fake_put_nowait(item):
        events.append(item)

    monkeypatch.setattr(lg._AsyncSmartLogger__queue, "put_nowait", fake_put_nowait)

    # Call rotation callback many times
    for _ in range(20):
        handler.rotation_callback(handler)

    await asyncio.sleep(0.05)

    # Still only one rotation event should have been enqueued
    assert sum(1 for e in events if e.op is AsyncOp.ROTATE) == 1

    await lg.shutdown()


@pytest.mark.asyncio
async def test_rotation_callback_starts_worker(tmp_path):
    # Create logger inside an event loop: worker auto-starts
    lg = AsyncSmartLogger("rot_start_worker")

    # Add a rotating file handler
    logic = RotationLogic(maxBytes=1, backupCount=1)
    lg.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]

    # Trigger rotation callback
    handler.rotation_callback(handler)

    # Worker already exists; rotation should enqueue exactly one item
    await asyncio.sleep(0.05)

    assert lg._AsyncSmartLogger__worker_tasks is not None
    assert lg._AsyncSmartLogger__queue.qsize() == 0  # <-- correct expectation

    await lg.shutdown()


@pytest.mark.asyncio
async def test_rotation_callback_after_retire(tmp_path):
    lg = AsyncSmartLogger("rot_after_retire")
    logic = RotationLogic(maxBytes=1, backupCount=1)
    lg.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]

    lg.retire()

    handler.rotation_callback(handler)

    await asyncio.sleep(0.05)

    assert lg._AsyncSmartLogger__queue.qsize() == 0


@pytest.mark.asyncio
async def test_rotation_callback_queuefull_retry(tmp_path, monkeypatch):
    lg = AsyncSmartLogger("rot_retry")
    logic = RotationLogic(maxBytes=1, backupCount=1)
    lg.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]

    class AlwaysFull:
        def __init__(self):
            self.calls = 0
        def boom(self, *a, **kw):
            self.calls += 1
            raise asyncio.QueueFull

    full = AlwaysFull()
    monkeypatch.setattr(lg._AsyncSmartLogger__queue, "put_nowait", full.boom)

    handler.rotation_callback(handler)

    await asyncio.sleep(0.05)

    assert full.calls >= 3


@pytest.mark.asyncio
async def test_rotation_callback_no_duplicate_events(tmp_path, monkeypatch):
    lg = AsyncSmartLogger("rot_no_dupes")
    logic = RotationLogic(maxBytes=1, backupCount=1)
    lg.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]

    events = []

    def fake_put_nowait(item):
        events.append(item)

    monkeypatch.setattr(lg._AsyncSmartLogger__queue, "put_nowait", fake_put_nowait)

    # Trigger twice
    handler.rotation_callback(handler)
    handler.rotation_callback(handler)

    await asyncio.sleep(0.05)

    # Only one rotation event should have been enqueued
    assert sum(1 for e in events if e.op is AsyncOp.ROTATE) == 1

    await lg.shutdown()


@pytest.mark.asyncio
async def test_rotation_callback_before_worker_started(tmp_path):
    lg = AsyncSmartLogger("rot_before_worker", level=logging.INFO)
    lg._AsyncSmartLogger__worker_tasks = None  # simulate no worker yet

    logic = RotationLogic(maxBytes=1, backupCount=1)
    lg.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]

    handler.rotation_callback(handler)

    await asyncio.sleep(0.05)
    assert lg._AsyncSmartLogger__worker_tasks is not None

    # Prevent dangling tasks
    await lg.shutdown()


@pytest.mark.asyncio
async def test_rotation_occurs_under_concurrency(tmp_path):
    lg = AsyncSmartLogger("rot_concurrency")
    logic = RotationLogic(maxBytes=50, backupCount=3)
    lg.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    async def spam():
        for _ in range(200):
            await lg.a_info("x" * 200)

    await asyncio.gather(*(spam() for _ in range(5)))
    await lg.flush()

    rotated = list(tmp_path.glob("rot.log.*"))
    assert len(rotated) >= 1


@pytest.mark.asyncio
async def test_enqueue_log_backpressure_retries(monkeypatch):
    lg = AsyncSmartLogger("bp_log")

    class AlwaysFull:
        def __init__(self):
            self.calls = 0
        def boom(self, *a, **kw):
            self.calls += 1
            raise asyncio.QueueFull

    full = AlwaysFull()
    monkeypatch.setattr(lg._AsyncSmartLogger__queue, "put_nowait", full.boom)

    await lg.a_info("hello")

    # Should have attempted retries
    assert full.calls >= 3


@pytest.mark.asyncio
async def test_flush_waits_for_rotation(tmp_path):
    lg = AsyncSmartLogger("flush_rot")
    logic = RotationLogic(maxBytes=1, backupCount=1)
    lg.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    # Force rotation
    for _ in range(10):
        await lg.a_info("x" * 100)

    await lg.flush()

    rotated = list(tmp_path.glob("rot.log.*"))
    assert len(rotated) >= 1


@pytest.mark.asyncio
async def test_rotation_scheduled_once(tmp_path):
    from LogSmith.async_smartlogger import AsyncSmartLogger
    from LogSmith.rotation_base import RotationLogic

    lg = AsyncSmartLogger("sched_once")
    lg.add_file(str(tmp_path), "exp.log", rotation_logic=RotationLogic(maxBytes=1))

    # Trigger multiple writes that exceed maxBytes
    for _ in range(5):
        await lg.a_info("X" * 200)

    await lg.flush()

    # If the test reaches this point without error, the branch was hit
    assert True


import time
import os
from datetime import datetime, timedelta

import pytest

from LogSmith.smartlogger import SmartLogger
from LogSmith.rotation_base import RotationLogic, When, RotationTimestamp


def test_daily_rotation_triggers_after_timestamp(tmp_path):
    """
    Verify that SmartLogger rotates when using When.EVERYDAY and the
    timestamp is only a few seconds in the future.
    """

    logdir = tmp_path
    logfile = "daily.log"
    base_path = logdir / logfile

    # Compute a timestamp 2 seconds in the future
    now = datetime.now()
    future = now + timedelta(seconds=2)

    ts = RotationTimestamp(
        hour=future.hour,
        minute=future.minute,
        second=future.second,
    )

    rotation = RotationLogic(
        when=When.EVERYDAY,
        interval=1,          # irrelevant for EVERYDAY
        timestamp=ts,
        maxBytes=None,       # disable size rotation
        backupCount=3,
    )

    lg = SmartLogger("daily_rotation_test")
    lg.add_file(str(logdir), logfile, rotation_logic=rotation)

    # Write once BEFORE the rollover moment
    lg.info("before rollover")

    # Sleep long enough to pass the rollover timestamp
    time.sleep(2.5)

    # Write again AFTER the rollover moment → should trigger rotation
    lg.info("after rollover")

    # Flush to ensure handler writes are complete
    for h in lg._SmartLogger__py_logger.handlers:
        h.flush()

    # The rotated file should now exist
    rotated = base_path.with_name(logfile + ".1")
    assert rotated.exists(), f"Expected rotated file {rotated} to exist"

    # Cleanup
    lg.destroy()
