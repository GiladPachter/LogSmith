import logging
import os
import time

from LogSmith import LargeLogEntryBehavior, ExpirationRule, ExpirationScale, When, RotationTimestamp
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler


def test_emit_preformatted_string(tmp_path):
    file = tmp_path / "x.log"
    h = Async_TimedSizedRotatingFileHandler(str(file), max_bytes=100)

    # Preformatted string path (not a LogRecord)
    h.emit("hello world")

    with open(file, "r") as f:
        assert "hello world" in f.read()


def test_large_entry_dump_silently(tmp_path):
    file = tmp_path / "x.log"
    h = Async_TimedSizedRotatingFileHandler(
        str(file),
        max_bytes=1,
        large_entry_behavior=LargeLogEntryBehavior.DumpSilently,
    )

    rec = logging.LogRecord("x", logging.INFO, __file__, 1, "hello", (), None)

    # Should not write, should schedule rotation
    h.emit(rec)
    assert os.path.getsize(file) == 0


import pytest

def test_large_entry_crash(tmp_path):
    file = tmp_path / "x.log"
    h = Async_TimedSizedRotatingFileHandler(
        str(file),
        max_bytes=1,
        large_entry_behavior=LargeLogEntryBehavior.Crash,
    )

    rec = logging.LogRecord("x", logging.INFO, __file__, 1, "hello", (), None)

    with pytest.raises(ValueError):
        h.emit(rec)


def test_large_entry_rotate_first(tmp_path):
    file = tmp_path / "x.log"
    h = Async_TimedSizedRotatingFileHandler(
        str(file),
        max_bytes=1,
        large_entry_behavior=LargeLogEntryBehavior.RotateFirst,
        backup_count=1,
    )

    rec = logging.LogRecord("x", logging.INFO, __file__, 1, "hello", (), None)

    h.emit(rec)

    # Rotation should have occurred
    rotated = tmp_path.glob("x.log.*")
    assert any(rotated)


def test_compute_next_rollover_second(tmp_path):
    h = Async_TimedSizedRotatingFileHandler(str(tmp_path / "x.log"), when=When.SECOND, interval=1)
    now = time.time()
    # noinspection PyUnresolvedReferences
    nxt = h._Async_TimedSizedRotatingFileHandler__compute_next_rollover(now)
    assert nxt > now


def test_expiration_rule_deletes_old_files(tmp_path):
    file = tmp_path / "x.log"
    h = Async_TimedSizedRotatingFileHandler(
        str(file),
        expiration_rule=ExpirationRule(ExpirationScale.Seconds, 0),
    )

    old = tmp_path / "x.log.1"
    old.write_text("old")
    os.utime(old, (time.time() - 9999, time.time() - 9999))

    # noinspection PyUnresolvedReferences
    h._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()

    assert not old.exists()


def test_rotation_suffix_pid_timestamp(tmp_path, monkeypatch):
    file = tmp_path / "x.log"
    h = Async_TimedSizedRotatingFileHandler(
        str(file),
        append_filename_pid=True,
        append_filename_timestamp=True,
    )

    # noinspection PyUnresolvedReferences
    suffix = h._Async_TimedSizedRotatingFileHandler__rotation_suffix()
    assert suffix.count(".") == 1  # pid.timestamp


def test_size_would_exceed(tmp_path):
    file = tmp_path / "x.log"
    h = Async_TimedSizedRotatingFileHandler(str(file), max_bytes=10)

    with open(file, "w") as f:
        f.write("12345")

    h.stream = open(file, "a")
    # noinspection PyUnresolvedReferences
    assert h._Async_TimedSizedRotatingFileHandler__size_would_exceed("123456")


def test_should_rotate_time(tmp_path, monkeypatch):
    file = tmp_path / "x.log"
    h = Async_TimedSizedRotatingFileHandler(
        str(file),
        when=When.SECOND,
        interval=1,
    )

    # Force rollover_at to be in the past
    monkeypatch.setattr(h, "_Async_TimedSizedRotatingFileHandler__rollover_at", time.time() - 10)

    # noinspection PyUnresolvedReferences
    assert h._Async_TimedSizedRotatingFileHandler__should_rotate("x")


def test_compute_next_rollover_weekday(tmp_path):
    h = Async_TimedSizedRotatingFileHandler(
        str(tmp_path / "x.log"),
        when=When.MONDAY,
        timestamp=RotationTimestamp(0, 0, 0),
    )

    now = time.time()
    # noinspection PyUnresolvedReferences
    nxt = h._Async_TimedSizedRotatingFileHandler__compute_next_rollover(now)
    assert nxt > now


def test_expiration_monthday(tmp_path):
    file = tmp_path / "x.log"
    h = Async_TimedSizedRotatingFileHandler(
        str(file),
        expiration_rule=ExpirationRule(ExpirationScale.MonthDay, 0),
    )

    old = tmp_path / "x.log.1"
    old.write_text("old")

    # Set mtime to yesterday
    yesterday = time.time() - 86400
    os.utime(old, (yesterday, yesterday))

    # noinspection PyUnresolvedReferences
    h._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()

    assert not old.exists()


def test_list_rotated_files(tmp_path):
    file = tmp_path / "x.log"
    h = Async_TimedSizedRotatingFileHandler(str(file))

    (tmp_path / "x.log.1").write_text("a")
    (tmp_path / "x.log.2").write_text("b")

    # noinspection PyUnresolvedReferences
    lst = h._Async_TimedSizedRotatingFileHandler__list_rotated_files()
    assert len(lst) == 3
