import asyncio
import os
import time
from datetime import datetime
import logging
from unittest.mock import MagicMock

import pytest

from LogSmith import AsyncSmartLogger
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.async_smartlogger import _QueueItem, AsyncOp
from LogSmith.formatter import StructuredPlainFormatter, LogRecordDetails
from LogSmith.rotation_base import (
    When,
    RotationTimestamp,
    ExpirationRule,
    ExpirationScale,
    LargeLogEntryBehavior,
)
from tests.helpers import DummyHandler


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def make_record(msg="hello"):
    return logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="x.py",
        lineno=10,
        msg=msg,
        args=(),
        exc_info=None,
    )


def write(handler, msg):
    """Emit a record synchronously."""
    rec = make_record(msg)
    handler.emit(rec)


async def drain(logger: AsyncSmartLogger):
    # noinspection PyProtectedMember
    q = logger._AsyncSmartLogger__queue
    await q.join()
    await asyncio.sleep(0)


# ------------------------------------------------------------
# 1. Size-based rotation scheduling + perform_rotation
# ------------------------------------------------------------

def test_size_rotation(tmp_path):
    file = tmp_path / "log.txt"

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(file),
        max_bytes=10,
        backup_count=3,
    )

    # rotation callback triggers immediate rotation
    handler.rotation_callback = lambda h: h.perform_rotation()

    write(handler, "12345")
    write(handler, "67890")  # triggers rotation

    assert file.read_text() == "67890\n"
    assert (tmp_path / "log.txt.1").read_text() == "12345\n"


# ------------------------------------------------------------
# 2. Large entry behavior: DROP
# ------------------------------------------------------------

def test_large_entry_drop(tmp_path):
    file = tmp_path / "log.txt"

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(file),
        max_bytes=5,
        large_entry_behavior=LargeLogEntryBehavior.DumpSilently,
    )

    write(handler, "X" * 20)  # too large → dropped

    assert file.read_text() == ""


# ------------------------------------------------------------
# 3. Large entry behavior: Crash
# ------------------------------------------------------------

def test_large_entry_crash(tmp_path):
    file = tmp_path / "log.txt"

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(file),
        max_bytes=5,
        large_entry_behavior=LargeLogEntryBehavior.Crash,
    )

    with pytest.raises(ValueError):
        write(handler, "X" * 20)


# ------------------------------------------------------------
# 4. Large entry behavior: RotateFirst
# ------------------------------------------------------------

def test_large_entry_rotate_first(tmp_path):
    file = tmp_path / "log.txt"

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(file),
        max_bytes=20,  # disable size-based rotation
        backup_count=2,
        large_entry_behavior=LargeLogEntryBehavior.RotateFirst,
    )

    formatter = StructuredPlainFormatter(LogRecordDetails())
    handler.setFormatter(formatter)

    write(handler, "BBBBBBBBBB")  # 10 bytes

    # RotateFirst → rotate BEFORE writing
    assert (tmp_path / "log.txt.1").exists()
    assert (tmp_path / "log.txt.1").read_text() == ""  # empty file
    assert (tmp_path / "log.txt").read_text(encoding="utf-8").endswith("BBBBBBBBBB\n")


def test_large_entry_exceed_if_empty(tmp_path):
    file = tmp_path / "log.txt"

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(file),
        max_bytes=0,  # disable size-based rotation
        backup_count=2,
        large_entry_behavior=LargeLogEntryBehavior.ExceedMaxBytesIfFileIsEmpty,
    )

    write(handler, "BBBBBBBBBB")  # 10 bytes

    # ExceedMaxBytesIfFileIsEmpty → file is empty → WRITE, no rotation
    assert not (tmp_path / "log.txt.1").exists()
    assert (tmp_path / "log.txt").read_text() == "BBBBBBBBBB\n"


# ------------------------------------------------------------
# 5. ExceedMaxBytesIfFileIsEmpty
# ------------------------------------------------------------

def test_large_entry_exceed_if_empty(tmp_path):
    file = tmp_path / "log.txt"

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(file),
        max_bytes=5,
        large_entry_behavior=LargeLogEntryBehavior.ExceedMaxBytesIfFileIsEmpty,
    )

    write(handler, "X" * 20)  # allowed because file is empty

    assert file.read_text() == "XXXXXXXXXXXXXXXXXXXX\n"


# ------------------------------------------------------------
# 6. Time-based rotation scheduling
# ------------------------------------------------------------

def test_time_rotation(tmp_path, monkeypatch):
    file = tmp_path / "log.txt"

    monkeypatch.setattr(time, "time", lambda: 1000)

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(file),
        when=When.SECOND,
        interval=1,
        backup_count=2,
    )

    handler.rotation_callback = lambda h: h.perform_rotation()

    write(handler, "A")

    monkeypatch.setattr(time, "time", lambda: 2000)
    write(handler, "B")

    # Correct behavior:
    # The entire file ("A\nB\n") is rotated into log.txt.1
    assert (tmp_path / "log.txt.1").read_text(encoding="utf-8") == "A\n"
    assert (tmp_path / "log.txt").read_text(encoding="utf-8") == "B\n"


# ------------------------------------------------------------
# 7. Expiration policy
# ------------------------------------------------------------

def test_expiration_policy(tmp_path):
    file = tmp_path / "log.txt"

    # Create old rotated files
    old1 = tmp_path / "log.txt.1"
    old2 = tmp_path / "log.txt.2"
    old1.write_text("old1")
    old2.write_text("old2")

    # Set their mtime to 2 hours ago
    old_time = time.time() - 7200
    os.utime(old1, (old_time, old_time))
    os.utime(old2, (old_time, old_time))

    rule = ExpirationRule(scale=ExpirationScale.Seconds, interval=3600)

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(file),
        expiration_rule=rule,
    )

    # Call the expiration logic directly to cover it
    # noinspection PyUnresolvedReferences
    handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()

    assert not old1.exists()
    assert not old2.exists()


# ------------------------------------------------------------
# 8. Rollover interval computation
# ------------------------------------------------------------

def test_rollover_interval_seconds():
    file = "dummy.txt"

    h = Async_TimedSizedRotatingFileHandler(filename=file, when=When.SECOND, interval=5)
    # noinspection PyUnresolvedReferences
    assert h._Async_TimedSizedRotatingFileHandler__rollover_interval_seconds() == 5

    h = Async_TimedSizedRotatingFileHandler(filename=file, when=When.MINUTE, interval=2)
    # noinspection PyUnresolvedReferences
    assert h._Async_TimedSizedRotatingFileHandler__rollover_interval_seconds() == 120

    h = Async_TimedSizedRotatingFileHandler(filename=file, when=When.HOUR, interval=1)
    # noinspection PyUnresolvedReferences
    assert h._Async_TimedSizedRotatingFileHandler__rollover_interval_seconds() == 3600


# ------------------------------------------------------------
# 9. Next rollover computation (daily)
# ------------------------------------------------------------

def test_compute_next_rollover_daily(monkeypatch):
    file = "dummy.txt"

    # Fake time: March 20 2026, 10:00:00
    fake_now = datetime(2026, 3, 20, 10, 0, 0).timestamp()
    monkeypatch.setattr(time, "time", lambda: fake_now)

    h = Async_TimedSizedRotatingFileHandler(
        filename=file,
        when=When.EVERYDAY,
        timestamp=RotationTimestamp(hour=9, minute=0, second=0),
    )

    # noinspection PyUnresolvedReferences
    next_roll = h._Async_TimedSizedRotatingFileHandler__compute_next_rollover(fake_now)

    # Should roll over next day at 09:00
    expected = datetime(2026, 3, 21, 9, 0, 0).timestamp()
    assert abs(next_roll - expected) < 1


# ------------------------------------------------------------
# 10. Reopen logic after external deletion
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_handler_exception_swallowed():
    logger = AsyncSmartLogger("test_exc")

    # Force worker creation manually
    loop = asyncio.get_running_loop()
    logger._AsyncSmartLogger__loop = loop
    logger._AsyncSmartLogger__worker_tasks = [
        loop.create_task(logger._AsyncSmartLogger__worker())
    ]

    bad = DummyHandler()
    bad.emit = MagicMock(side_effect=RuntimeError("boom"))

    good = DummyHandler()

    # Good first, then bad
    logger._AsyncSmartLogger__py_logger.addHandler(good)
    logger._AsyncSmartLogger__py_logger.addHandler(bad)

    item = _QueueItem(
        op=AsyncOp.LOG,
        payload={
            "level": logging.ERROR,
            "msg": "oops",
            "args": (),
            "extra": {},
            "fields": {},
            "exc_info": None,
            "stack_info_flag": False,
            "pathname": __file__,
            "lineno": 20,
            "func_name": "test_handler_exception_swallowed",
            "stack_info": None,
        },
    )
    logger._AsyncSmartLogger__queue.put_nowait(item)

    await drain(logger)

    assert good.records == ["oops"]

    logger.destroy()
