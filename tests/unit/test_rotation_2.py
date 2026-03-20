import os
import logging
import datetime
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from LogSmith.rotation import ConcurrentTimedSizedRotatingFileHandler
from LogSmith.rotation_base import (
    When, RotationTimestamp, ExpirationRule, ExpirationScale,
    LargeLogEntryBehavior
)


def make_handler(tmp_path, **kwargs):
    file = tmp_path / "test.log"
    return ConcurrentTimedSizedRotatingFileHandler(str(file), **kwargs)


# ----------------------------------------------------------------------
# 1. No-lock fallback (line 16)
# ----------------------------------------------------------------------
def test_no_locking(monkeypatch, tmp_path):
    monkeypatch.setattr("LogSmith.rotation._HAS_FCNTL", False)
    monkeypatch.setattr("LogSmith.rotation._HAS_MSVCRT", False)

    handler = make_handler(tmp_path)
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", (), None)

    handler.emit(record)  # should not crash


# ----------------------------------------------------------------------
# 2. Initial rollover logic (106->exit, 121, 123)
# ----------------------------------------------------------------------
def test_initial_rollover_daily(tmp_path):
    handler = make_handler(
        tmp_path,
        when=When.EVERYDAY,
        timestamp=RotationTimestamp(0, 0, 0),
    )
    # noinspection PyUnresolvedReferences
    assert handler._ConcurrentTimedSizedRotatingFileHandler__rollover_at is not None


# ----------------------------------------------------------------------
# 3. WEEKDAY rotation (141–147)
# ----------------------------------------------------------------------
def test_weekday_rollover(monkeypatch, tmp_path):
    class FakeDT(datetime.datetime):
        # noinspection PyMethodOverriding
        @classmethod
        def fromtimestamp(cls, ts):
            return cls(2024, 1, 2)  # Tuesday

    monkeypatch.setattr(datetime, "datetime", FakeDT)

    handler = make_handler(tmp_path, when=When.MONDAY)
    handler._ConcurrentTimedSizedRotatingFileHandler__rollover_at = 0

    record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", (), None)
    handler.emit(record)


# ----------------------------------------------------------------------
# 4. Time-based rollover (161)
# ----------------------------------------------------------------------
def test_time_based_rollover(tmp_path):
    handler = make_handler(tmp_path, when=When.SECOND)
    handler._ConcurrentTimedSizedRotatingFileHandler__rollover_at = 0

    record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", (), None)
    handler.emit(record)


# ----------------------------------------------------------------------
# 5. file_empty exception path (180)
# ----------------------------------------------------------------------
def test_file_empty_exception(tmp_path):
    handler = make_handler(tmp_path, max_bytes=5)
    handler.stream.tell = MagicMock(side_effect=OSError("boom"))

    record = logging.LogRecord("x", logging.INFO, __file__, 1, "123456789", (), None)
    handler.emit(record)  # should not crash


# ----------------------------------------------------------------------
# 6. ExceedMaxBytesIfFileIsEmpty (186–189)
# ----------------------------------------------------------------------
def test_large_entry_exceed_empty(tmp_path):
    handler = make_handler(tmp_path, max_bytes=5)
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "123456789", (), None)
    handler.emit(record)


# ----------------------------------------------------------------------
# 7. RotateFirst, DumpSilently, Crash (204->206, 221)
# ----------------------------------------------------------------------
def test_large_entry_rotate_first(tmp_path):
    handler = make_handler(
        tmp_path,
        max_bytes=5,
        large_entry_behavior=LargeLogEntryBehavior.RotateFirst,
    )
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "123456789", (), None)
    handler.emit(record)


def test_large_entry_dump_silently(tmp_path):
    handler = make_handler(
        tmp_path,
        max_bytes=5,
        large_entry_behavior=LargeLogEntryBehavior.DumpSilently,
    )
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "123456789", (), None)
    handler.emit(record)
    assert Path(handler.baseFilename).read_text() == ""


def test_large_entry_crash(tmp_path):
    handler = make_handler(
        tmp_path,
        max_bytes=5,
        large_entry_behavior=LargeLogEntryBehavior.Crash,
    )
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "123456789", (), None)
    with pytest.raises(ValueError):
        handler.emit(record)


# ----------------------------------------------------------------------
# 8. filter(record) == False (233)
# ----------------------------------------------------------------------
def test_filter_false(tmp_path):
    handler = make_handler(tmp_path)
    handler.addFilter(lambda r: False)

    record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", (), None)
    handler.emit(record)

    assert Path(handler.baseFilename).read_text() == ""


# ----------------------------------------------------------------------
# 9. PermissionError during rotation (307)
# ----------------------------------------------------------------------
def test_permission_error(monkeypatch, tmp_path):
    monkeypatch.setattr(os, "replace", MagicMock(side_effect=PermissionError))

    handler = make_handler(tmp_path, max_bytes=1)
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", (), None)

    handler.emit(record)  # should not crash


# ----------------------------------------------------------------------
# 10. ExpirationRule branches (349–354, 354–382, 365)
# ----------------------------------------------------------------------
@pytest.mark.parametrize("scale", [
    ExpirationScale.Seconds,
    ExpirationScale.Minutes,
    ExpirationScale.Hours,
    ExpirationScale.Days,
    ExpirationScale.MonthDay,
])
def test_expiration_rules(tmp_path, scale):
    handler = make_handler(
        tmp_path,
        expiration_rule=ExpirationRule(scale, 0),
    )

    old = tmp_path / "test.log.1"
    old.write_text("x")
    os.utime(old, (0, 0))  # very old

    # noinspection PyUnresolvedReferences
    handler._ConcurrentTimedSizedRotatingFileHandler__apply_expiration_policy()

    assert not old.exists()


def test_expiration_none(tmp_path):
    handler = make_handler(tmp_path, expiration_rule=None)
    # noinspection PyUnresolvedReferences
    handler._ConcurrentTimedSizedRotatingFileHandler__apply_expiration_policy()  # no-op


# ----------------------------------------------------------------------
# 11. Deletion failure (371–382)
# ----------------------------------------------------------------------
def test_expiration_delete_failure(monkeypatch, tmp_path):
    handler = make_handler(
        tmp_path,
        expiration_rule=ExpirationRule(ExpirationScale.Seconds, 0),
    )

    old = tmp_path / "test.log.1"
    old.write_text("x")
    os.utime(old, (0, 0))

    monkeypatch.setattr(os, "remove", MagicMock(side_effect=OSError("boom")))

    # noinspection PyUnresolvedReferences
    handler._ConcurrentTimedSizedRotatingFileHandler__apply_expiration_policy()

    # File should still exist
    assert old.exists()


# ----------------------------------------------------------------------
# 12. list_rotated_files (401–409)
# ----------------------------------------------------------------------
def test_list_rotated_files(tmp_path):
    handler = make_handler(tmp_path)

    (tmp_path / "test.log").write_text("x")
    (tmp_path / "test.log.1").write_text("x")
    (tmp_path / "test.log.lock").write_text("x")

    # noinspection PyUnresolvedReferences
    files = handler._ConcurrentTimedSizedRotatingFileHandler__list_rotated_files()

    assert any(f.endswith("test.log") for f in files)
    assert any(f.endswith("test.log.1") for f in files)
    assert all(not f.endswith(".lock") for f in files)
