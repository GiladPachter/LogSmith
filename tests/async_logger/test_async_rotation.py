import os
import time
import logging
from unittest.mock import Mock, patch

import pytest

from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.rotation_base import LargeLogEntryBehavior, ExpirationRule, ExpirationScale
from LogSmith.rotation_base import When


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def make_handler(tmp_path, **kwargs):
    file = tmp_path / "test.log"
    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(file),
        **kwargs
    )
    # Ensure stream is open
    if handler.stream is None:
        handler.stream = handler._open()
    return handler, file


def write(handler, msg="x"):
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
        func="f",
        sinfo=None,
    )
    handler.emit(record)


# ----------------------------------------------------------------------
# 1. Size-based rotation triggers callback
# ----------------------------------------------------------------------

def test_size_based_rotation_triggers_callback(tmp_path):
    handler, file = make_handler(tmp_path, max_bytes=20)

    cb = Mock()
    handler.rotation_callback = cb

    write(handler, "A" * 50)

    cb.assert_called_once()


# ----------------------------------------------------------------------
# 2. Large entry behavior — DROP
# ----------------------------------------------------------------------

def test_large_entry_drop(tmp_path):
    handler, file = make_handler(
        tmp_path,
        max_bytes=10,
        large_entry_behavior=LargeLogEntryBehavior.DumpSilently,
    )

    cb = Mock()
    handler.rotation_callback = cb

    write(handler, "X" * 100)

    # Rotation SHOULD be called
    cb.assert_called_once()

    # But file should remain empty
    assert file.read_text() == ""



# ----------------------------------------------------------------------
# 3. Large entry behavior — Crash
# ----------------------------------------------------------------------

def test_large_entry_crash(tmp_path):
    handler, file = make_handler(
        tmp_path,
        max_bytes=10,
        large_entry_behavior=LargeLogEntryBehavior.Crash,
    )

    with pytest.raises(ValueError):
        write(handler, "X" * 100)


# ----------------------------------------------------------------------
# 4. Large entry behavior — RotateFirst
# ----------------------------------------------------------------------

def test_large_entry_rotate_first(tmp_path):
    handler, file = make_handler(
        tmp_path,
        max_bytes=10,
        large_entry_behavior=LargeLogEntryBehavior.RotateFirst,
    )

    cb = Mock()
    handler.rotation_callback = cb

    write(handler, "X" * 100)

    cb.assert_called_once()
    assert file.read_text() != ""


# ----------------------------------------------------------------------
# 5. ExceedMaxBytesIfFileIsEmpty
# ----------------------------------------------------------------------

def test_large_entry_exceed_if_empty(tmp_path):
    handler, file = make_handler(
        tmp_path,
        max_bytes=10,
        large_entry_behavior=LargeLogEntryBehavior.ExceedMaxBytesIfFileIsEmpty,
    )

    cb = Mock()
    handler.rotation_callback = cb

    # First write
    write(handler, "X" * 100)
    cb.assert_called_once()

    # Simulate worker performing rotation
    handler.perform_rotation()
    assert cb.call_count == 1  # still 1, rotation callback is not called here

    # Second write
    write(handler, "X" * 100)
    assert cb.call_count == 2


# ----------------------------------------------------------------------
# 6. Time-based rotation triggers callback
# ----------------------------------------------------------------------

def test_time_based_rotation(tmp_path):
    cb = Mock()

    # 7 calls to time.time():
    # init, emit1(x2), perform_rotation(x2), emit2(x2)
    with patch("time.time", side_effect=[0, 0, 0, 1, 1, 2, 2]):
        handler, file = make_handler(
            tmp_path,
            when=When.SECOND,
            interval=1,
        )

        handler.rotation_callback = cb

        write(handler, "hello")

        handler.perform_rotation()

        write(handler, "hello again")

    assert cb.call_count == 1


# ----------------------------------------------------------------------
# 7. Throttled time-based rotation (0.25s check)
# ----------------------------------------------------------------------

def test_time_based_throttle(tmp_path):
    handler, file = make_handler(
        tmp_path,
        when=When.SECOND,
        interval=1,
    )

    cb = Mock()
    handler.rotation_callback = cb

    # emit() never performs time-based rotation
    with patch("time.time", side_effect=[0, 0, 0.3]):
        write(handler, "a")
        write(handler, "b")

    # No rotation should occur
    cb.assert_not_called()


# ----------------------------------------------------------------------
# 8. perform_rotation renames backups correctly
# ----------------------------------------------------------------------

def test_perform_rotation_backup_renaming(tmp_path):
    base = tmp_path / "test.log"
    base.write_text("old")

    # Create backups
    (tmp_path / "test.log.1").write_text("one")
    (tmp_path / "test.log.2").write_text("two")

    handler, file = make_handler(tmp_path)
    handler.baseFilename = str(base)

    handler.perform_rotation()

    assert (tmp_path / "test.log.3").exists()
    assert (tmp_path / "test.log.2").exists()
    assert (tmp_path / "test.log.1").exists()


# ----------------------------------------------------------------------
# 9. perform_rotation reopens stream
# ----------------------------------------------------------------------

def test_perform_rotation_reopens_stream(tmp_path):
    handler, file = make_handler(tmp_path)

    handler.stream.close()
    handler.stream = None

    handler.perform_rotation()

    assert handler.stream is not None
    assert not handler.stream.closed


# ----------------------------------------------------------------------
# 10. perform_rotation updates rollover_at
# ----------------------------------------------------------------------

def test_perform_rotation_updates_rollover(tmp_path):
    handler, file = make_handler(
        tmp_path,
        when=When.SECOND,
        interval=1,
    )

    handler: Async_TimedSizedRotatingFileHandler

    # before = handler.__rollover_at
    # noinspection PyUnresolvedReferences
    before = handler._Async_TimedSizedRotatingFileHandler__rollover_at
    handler.perform_rotation()
    # after = handler.__rollover_at
    # noinspection PyUnresolvedReferences
    after = handler._Async_TimedSizedRotatingFileHandler__rollover_at

    assert before != after


# ----------------------------------------------------------------------
# 11. expiration policy deletes old files
# ----------------------------------------------------------------------

def test_expiration_policy(tmp_path):
    base = tmp_path / "test.log"
    base.write_text("base")

    old_file = tmp_path / "test.log.1"
    old_file.write_text("old")

    old_ts = time.time() - 1000
    os.utime(old_file, (old_ts, old_ts))

    handler, file = make_handler(
        tmp_path,
        expiration_rule=ExpirationRule(
            scale=ExpirationScale.Seconds,
            interval=1,
        ),
    )

    handler.perform_rotation()

    # After rotation:
    # test.log.1 is the newly rotated active file
    # test.log.2 is the old_file we created
    expired = tmp_path / "test.log.2"

    assert not expired.exists()


# ----------------------------------------------------------------------
# 12. _list_rotated_files returns correct list
# ----------------------------------------------------------------------

def test_list_rotated_files(tmp_path):
    base = tmp_path / "test.log"
    base.write_text("x")

    (tmp_path / "test.log.1").write_text("1")
    (tmp_path / "test.log.2").write_text("2")
    (tmp_path / "test.log.lock").write_text("lock")

    handler, file = make_handler(tmp_path)
    handler.baseFilename = str(base)

    files = handler._list_rotated_files()

    assert str(tmp_path / "test.log.1") in files
    assert str(tmp_path / "test.log.2") in files
    assert str(tmp_path / "test.log.lock") not in files
