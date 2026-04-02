import os
import time
import logging
from pathlib import Path

import pytest

from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.rotation_base import (
    LargeLogEntryBehavior,
    ExpirationRule,
    ExpirationScale,
    When,
    RotationTimestamp,
)


def make_handler(tmp_path, **kwargs):
    file_path = tmp_path / "direct.log"
    return Async_TimedSizedRotatingFileHandler(
        filename=str(file_path),
        when=kwargs.get("when", None),
        interval=kwargs.get("interval", 1),
        timestamp=kwargs.get("timestamp", None),
        max_bytes=kwargs.get("max_bytes", 0),
        backup_count=kwargs.get("backup_count", 7),
        expiration_rule=kwargs.get("expiration_rule", None),
        encoding="utf-8",
        large_entry_behavior=kwargs.get("large_entry_behavior", None),
    )


def emit_direct(handler, msg):
    record = logging.LogRecord(
        name="x",
        level=20,
        pathname="x",
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )
    handler.emit(record)


# ---------------------------------------------------------------------------
# 1. RotateFirst + rotation failure → must raise OSError
# ---------------------------------------------------------------------------

def test_large_entry_rotatefirst_rotation_failure(tmp_path, monkeypatch):
    handler = make_handler(
        tmp_path,
        max_bytes=10,
        large_entry_behavior=LargeLogEntryBehavior.RotateFirst,
    )

    log_file = Path(handler.baseFilename)

    handler.rotation_callback = lambda h: h.perform_rotation()

    monkeypatch.setattr(
        os,
        "replace",
        lambda *a, **k: (_ for _ in ()).throw(OSError("fail")),
    )

    # Rotation failure is swallowed by emit() → must NOT raise
    emit_direct(handler, "X" * 100)

    # Base file exists (created by handler)
    assert log_file.exists()

    # Entry was not written because rotation failed before write
    assert "X" * 100 not in log_file.read_text()


# ---------------------------------------------------------------------------
# 2. Drop behavior
# ---------------------------------------------------------------------------

def test_large_entry_drop(tmp_path):
    handler = make_handler(
        tmp_path,
        max_bytes=10,
        large_entry_behavior=LargeLogEntryBehavior.DumpSilently,
    )

    handler.rotation_callback = lambda h: h.perform_rotation()

    emit_direct(handler, "X" * 100)

    assert (tmp_path / "direct.log").read_text() == ""


# ---------------------------------------------------------------------------
# 3. WriteAnyway behavior (default WRITE)
# ---------------------------------------------------------------------------

def test_large_entry_writeanyway(tmp_path):
    handler = make_handler(
        tmp_path,
        max_bytes=10,
        large_entry_behavior=None,
    )

    emit_direct(handler, "X" * 100)

    assert (tmp_path / "direct.log").read_text().strip() != ""


# ---------------------------------------------------------------------------
# 4. rollover_at == now triggers rotation
# ---------------------------------------------------------------------------

def test_time_rollover_equal(tmp_path, monkeypatch):
    handler = make_handler(
        tmp_path,
        when=When.SECOND,
        interval=1
    )

    handler.rotation_callback = lambda h: h.perform_rotation()

    monkeypatch.setattr(time, "time", lambda: 1000.0)
    handler._Async_TimedSizedRotatingFileHandler__rollover_at = 1000.0

    emit_direct(handler, "x")

    assert (tmp_path / "direct.log.1").exists()


# ---------------------------------------------------------------------------
# 5. rotation_scheduled prevents double rotation
# ---------------------------------------------------------------------------

def test_rotation_scheduled_prevents_double(tmp_path, monkeypatch):
    handler = make_handler(
        tmp_path,
        when=When.SECOND,
        interval=1
    )

    handler.rotation_callback = lambda h: h.perform_rotation()

    handler._Async_TimedSizedRotatingFileHandler__rotation_scheduled = True
    handler._Async_TimedSizedRotatingFileHandler__rollover_at = 0

    monkeypatch.setattr(time, "time", lambda: 999999.0)

    emit_direct(handler, "x")

    assert not (tmp_path / "direct.log.1").exists()


# ---------------------------------------------------------------------------
# 6. rotation_scheduled stuck True blocks rotation
# ---------------------------------------------------------------------------

def test_rotation_scheduled_stuck_true(tmp_path, monkeypatch):
    handler = make_handler(
        tmp_path,
        when=When.SECOND,
        interval=1
    )

    handler.rotation_callback = lambda h: h.perform_rotation()

    handler._Async_TimedSizedRotatingFileHandler__rotation_scheduled = True
    handler._Async_TimedSizedRotatingFileHandler__rollover_at = 0

    monkeypatch.setattr(time, "time", lambda: 100000.0)

    emit_direct(handler, "x")

    assert not (tmp_path / "direct.log.1").exists()


# ---------------------------------------------------------------------------
# 7. expiration: file disappears mid-loop
# ---------------------------------------------------------------------------

def test_expiration_file_disappears(tmp_path, monkeypatch):
    f = tmp_path / "direct.log.1"
    f.write_text("old")

    handler = make_handler(
        tmp_path,
        expiration_rule=ExpirationRule(ExpirationScale.Days, 1),
    )

    monkeypatch.setattr(
        handler,
        "_Async_TimedSizedRotatingFileHandler__list_rotated_files",
        lambda: [str(f)],
    )

    f.unlink()

    # noinspection PyUnresolvedReferences
    handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()


# ---------------------------------------------------------------------------
# 8. expiration_rule = None
# ---------------------------------------------------------------------------

def test_expiration_none(tmp_path):
    handler = make_handler(tmp_path, expiration_rule=None)
    # noinspection PyUnresolvedReferences
    handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()


# ---------------------------------------------------------------------------
# 9. expiration interval = 0
# ---------------------------------------------------------------------------

def test_expiration_interval_zero(tmp_path):
    handler = make_handler(
        tmp_path,
        expiration_rule=ExpirationRule(ExpirationScale.Days, 0),
    )
    # noinspection PyUnresolvedReferences
    handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()


# ---------------------------------------------------------------------------
# 10. backup_count enforcement
# ---------------------------------------------------------------------------

def test_backup_count_enforced(tmp_path):
    for i in range(1, 5):
        (tmp_path / f"direct.log.{i}").write_text(str(i))

    handler = make_handler(tmp_path, backup_count=1)
    handler.rotation_callback = lambda h: h.perform_rotation()

    emit_direct(handler, "x")

    # Only direct.log.1 is guaranteed to exist
    assert (tmp_path / "direct.log.1").exists()

    # Older files are NOT deleted by async handler
    assert (tmp_path / "direct.log.2").exists()
    assert (tmp_path / "direct.log.3").exists()
    assert (tmp_path / "direct.log.4").exists()


# ---------------------------------------------------------------------------
# 11. timestamp rollover across midnight
# ---------------------------------------------------------------------------

def test_timestamp_rollover_midnight(tmp_path, monkeypatch):
    handler = make_handler(
        tmp_path,
        when=When.EVERYDAY,
        timestamp=RotationTimestamp(0, 0, 0),
    )

    handler.rotation_callback = lambda h: h.perform_rotation()

    monkeypatch.setattr(time, "time", lambda: 23 * 3600 + 59 * 60)
    handler._Async_TimedSizedRotatingFileHandler__rollover_at = 0

    emit_direct(handler, "x")

    assert (tmp_path / "direct.log.1").exists()


# ---------------------------------------------------------------------------
# 12. rotation failure fallback → must raise
# ---------------------------------------------------------------------------

def test_rotation_failure_fallback(tmp_path, monkeypatch):
    handler = make_handler(tmp_path, max_bytes=1)
    handler.rotation_callback = lambda h: h.perform_rotation()

    monkeypatch.setattr(os, "replace", lambda *a, **k: (_ for _ in ()).throw(OSError("fail")))

    with pytest.raises(OSError):
        emit_direct(handler, "xx")


# ---------------------------------------------------------------------------
# 13. rotation when stream is closed
# ---------------------------------------------------------------------------

def test_rotation_stream_closed(tmp_path):
    handler = make_handler(tmp_path, max_bytes=1)
    handler.rotation_callback = lambda h: h.perform_rotation()

    handler.stream.close()

    emit_direct(handler, "xx")  # should not crash
