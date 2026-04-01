import logging
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.rotation_base import LargeLogEntryBehavior


class DummyCallback:
    def __init__(self):
        self.called_with = []

    def __call__(self, handler):
        self.called_with.append(handler)


def make_handler(tmp_path, behavior, max_bytes=10):
    log_file = Path(tmp_path) / "large_entry.log"
    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(log_file),
        max_bytes=max_bytes,
        large_entry_behavior=behavior,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler, log_file


@pytest.mark.asyncio
async def test_large_entry_dump_silently(tmp_path):
    cb = DummyCallback()
    handler, log_file = make_handler(tmp_path, LargeLogEntryBehavior.DumpSilently, max_bytes=5)
    handler.rotation_callback = cb

    record = logging.LogRecord(
        name="x",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="123456789",
        args=(),
        exc_info=None,
    )

    handler.emit(record)

    # Rotation IS scheduled (size check happens before DROP)
    assert cb.called_with == [handler]

    # But the entry is dropped → file remains empty or nonexistent
    assert not log_file.exists() or log_file.read_text() == ""


@pytest.mark.asyncio
async def test_large_entry_crash(tmp_path):
    handler, _ = make_handler(tmp_path, LargeLogEntryBehavior.Crash, max_bytes=5)

    record = logging.LogRecord(
        name="x",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="123456789",
        args=(),
        exc_info=None,
    )

    with pytest.raises(ValueError):
        handler.emit(record)


@pytest.mark.asyncio
async def test_large_entry_rotate_first(tmp_path):
    cb = DummyCallback()
    handler, log_file = make_handler(
        tmp_path,
        LargeLogEntryBehavior.RotateFirst,
        max_bytes=5,
    )
    handler.rotation_callback = cb

    record = logging.LogRecord(
        name="x",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="123456789",
        args=(),
        exc_info=None,
    )

    handler.emit(record)

    # RotateFirst rotates synchronously → callback is NOT used
    assert cb.called_with == []

    # The rotated file must exist
    rotated = tmp_path / "large_entry.log.1"
    assert rotated.exists()

    # And the entry was written to the new base file
    assert log_file.exists()
    assert "123456789" in log_file.read_text()


@pytest.mark.asyncio
async def test_large_entry_exceed_if_empty(tmp_path):
    cb = DummyCallback()
    handler, log_file = make_handler(
        tmp_path,
        LargeLogEntryBehavior.ExceedMaxBytesIfFileIsEmpty,
        max_bytes=5,
    )
    handler.rotation_callback = cb

    # First large write: file is empty → allowed, rotation scheduled
    rec1 = logging.LogRecord(
        name="x",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="123456789",
        args=(),
        exc_info=None,
    )
    handler.emit(rec1)

    assert log_file.exists()
    assert "123456789" in log_file.read_text()

    # Rotation callback fired once
    assert cb.called_with == [handler]

    # Second large write: file is non-empty → rotate-then-write
    rec2 = logging.LogRecord(
        name="x",
        level=logging.INFO,
        pathname=__file__,
        lineno=2,
        msg="abcdefghi",
        args=(),
        exc_info=None,
    )
    handler.emit(rec2)

    # BUT rotation is not executed (no worker), so __rotation_scheduled stays True
    # → no second callback
    assert cb.called_with == [handler]


import logging
from pathlib import Path
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler

def test_rotation_backup_shift(tmp_path):
    base = Path(tmp_path) / "app.log"

    # Create fake existing rotated files: app.log.1, app.log.2
    (tmp_path / "app.log").write_text("oldbase")
    (tmp_path / "app.log.1").write_text("one")
    (tmp_path / "app.log.2").write_text("two")

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(base),
        max_bytes=10,
        backup_count=3,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))

    # Force rotation
    handler.perform_rotation()

    # After rotation:
    # app.log.3 ← old app.log.2
    # app.log.2 ← old app.log.1
    # app.log.1 ← old base file
    assert (tmp_path / "app.log.3").read_text() == "two"
    assert (tmp_path / "app.log.2").read_text() == "one"
    assert (tmp_path / "app.log.1").read_text() == "oldbase"

    # New base file exists and is empty
    assert (tmp_path / "app.log").exists()
    assert (tmp_path / "app.log").read_text() == ""


import time
# from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.rotation_base import When, RotationTimestamp


def test_rollover_every_second():
    handler = Async_TimedSizedRotatingFileHandler(
        filename="dummy.log",
        when=When.SECOND,
        interval=1,
    )

    now = time.time()
    # noinspection PyUnresolvedReferences
    nxt = handler._Async_TimedSizedRotatingFileHandler__compute_next_rollover(now)

    # Should be exactly 1 second ahead
    assert abs(nxt - (now + 1)) < 0.01


def test_rollover_every_day_specific_time():
    ts = RotationTimestamp(hour=3, minute=30, second=0)

    handler = Async_TimedSizedRotatingFileHandler(
        filename="dummy.log",
        when=When.EVERYDAY,
        timestamp=ts,
    )

    # Fake "now" at 02:00
    now_dt = datetime(2024, 1, 1, 2, 0, 0)
    now = now_dt.timestamp()

    # noinspection PyUnresolvedReferences
    nxt = handler._Async_TimedSizedRotatingFileHandler__compute_next_rollover(now)
    nxt_dt = datetime.fromtimestamp(nxt)

    assert nxt_dt.hour == 3
    assert nxt_dt.minute == 30
    assert nxt_dt.date() == now_dt.date()  # same day


def test_rollover_every_day_next_day():
    ts = RotationTimestamp(hour=3, minute=30, second=0)

    handler = Async_TimedSizedRotatingFileHandler(
        filename="dummy.log",
        when=When.EVERYDAY,
        timestamp=ts,
    )

    # Fake "now" at 05:00 → target already passed
    now_dt = datetime(2024, 1, 1, 5, 0, 0)
    now = now_dt.timestamp()

    # noinspection PyUnresolvedReferences
    nxt = handler._Async_TimedSizedRotatingFileHandler__compute_next_rollover(now)
    nxt_dt = datetime.fromtimestamp(nxt)

    assert nxt_dt.hour == 3
    assert nxt_dt.minute == 30
    assert nxt_dt.date() == (now_dt + timedelta(days=1)).date()


def test_rollover_next_monday():
    ts = RotationTimestamp(hour=0, minute=0, second=0)

    handler = Async_TimedSizedRotatingFileHandler(
        filename="dummy.log",
        when=When.MONDAY,
        timestamp=ts,
    )

    # Fake "now" on Wednesday
    now_dt = datetime(2024, 1, 3, 12, 0, 0)  # Wednesday
    now = now_dt.timestamp()

    # noinspection PyUnresolvedReferences
    nxt = handler._Async_TimedSizedRotatingFileHandler__compute_next_rollover(now)
    nxt_dt = datetime.fromtimestamp(nxt)

    assert nxt_dt.weekday() == 0  # Monday
    assert nxt_dt > now_dt


def test_rollover_next_week_if_today_passed():
    ts = RotationTimestamp(hour=3, minute=0, second=0)

    handler = Async_TimedSizedRotatingFileHandler(
        filename="dummy.log",
        when=When.WEDNESDAY,
        timestamp=ts,
    )

    # Fake "now" Wednesday at 5am → target passed
    now_dt = datetime(2024, 1, 3, 5, 0, 0)  # Wednesday
    now = now_dt.timestamp()

    # noinspection PyUnresolvedReferences
    nxt = handler._Async_TimedSizedRotatingFileHandler__compute_next_rollover(now)
    nxt_dt = datetime.fromtimestamp(nxt)

    # Should be next Wednesday
    assert nxt_dt.date() == (now_dt + timedelta(days=7)).date()
    assert nxt_dt.hour == 3


