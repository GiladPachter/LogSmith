import os
import time
import logging
from pathlib import Path

import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.rotation_base import (
    When,
    RotationTimestamp,
    ExpirationRule,
    ExpirationScale,
    LargeLogEntryBehavior, RotationLogic,
)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

async def async_log(logger, msg):
    """Helper to ensure async logging completes."""
    await logger.a_info(msg)
    await asyncio.sleep(0.05)


# -------------------------------------------------------------------
# SECTION 1 — PUBLIC API TESTS (AsyncSmartLogger)
# -------------------------------------------------------------------
# These tests hit all branches reachable through the public API.
# -------------------------------------------------------------------

import asyncio

@pytest.mark.asyncio
async def test_async_rotation_size_based(tmp_path):
    logger = AsyncSmartLogger("async_rot_size")
    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="app.log",
        rotation_logic=RotationLogic(maxBytes=20),  # no time-based rotation
    )

    # Make file tiny to force rotation
    real_handler = next(h for h in logger._AsyncSmartLogger__py_logger.handlers if hasattr(h, "baseFilename"))
    real_handler.max_bytes = 20

    # Log enough to exceed size
    await logger.a_info("X" * 50)
    await asyncio.sleep(0.1)
    await logger.flush()

    assert (tmp_path / "app.log.1").exists()


@pytest.mark.asyncio
async def test_async_rotation_time_based(tmp_path, monkeypatch):
    logger = AsyncSmartLogger("async_rot_time")

    # Time-based rotation every second
    from LogSmith.rotation_base import RotationLogic
    rl = RotationLogic(when=When.SECOND, interval=1)

    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="app.log",
        rotation_logic=rl,
    )

    # Force rollover_at to be in the past
    real_handler = next(h for h in logger._AsyncSmartLogger__py_logger.handlers if hasattr(h, "baseFilename"))
    monkeypatch.setattr(time, "time", lambda: 1000.0)
    real_handler._Async_TimedSizedRotatingFileHandler__rollover_at = 999.0

    await logger.a_info("hello")
    await asyncio.sleep(0.1)

    assert (tmp_path / "app.log.1").exists()


@pytest.mark.asyncio
async def test_async_rotation_expiration(tmp_path, monkeypatch):
    logger = AsyncSmartLogger("async_rot_expire")

    from LogSmith.rotation_base import RotationLogic, ExpirationRule, ExpirationScale

    rl = RotationLogic(
        maxBytes=1,
        expiration_rule=ExpirationRule(ExpirationScale.Days, interval=1),
    )

    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="app.log",
        rotation_logic=rl,
    )

    # First rotation: create app.log.1
    await logger.a_info("X" * 50)
    await logger.flush()

    rotated1 = tmp_path / "app.log.1"
    assert rotated1.exists()

    # Age it artificially
    two_days_ago = time.time() - 2 * 86400
    os.utime(rotated1, (two_days_ago, two_days_ago))

    # Get the real handler
    real_handler = next(
        h for h in logger._AsyncSmartLogger__py_logger.handlers
        if hasattr(h, "baseFilename")
    )

    # Monkeypatch list_rotated_files to return only the aged file
    monkeypatch.setattr(
        real_handler,
        "_Async_TimedSizedRotatingFileHandler__list_rotated_files",
        lambda: [str(rotated1)],
    )

    # Call expiration directly (no second rotation)
    real_handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()

    assert not rotated1.exists()


# -------------------------------------------------------------------
# SECTION 2 — DIRECT HANDLER TESTS (Unreachable via public API)
# -------------------------------------------------------------------
# These tests hit branches that SmartLogger/AsyncSmartLogger cannot reach.
# -------------------------------------------------------------------

def make_handler(tmp_path, **kwargs):
    file_path = tmp_path / "direct.log"
    return Async_TimedSizedRotatingFileHandler(str(file_path), **kwargs)


def emit_direct(handler, msg):
    """Emit directly to handler (only for unreachable branches)."""
    logger = logging.getLogger("direct.asyncrot")
    record = logger.makeRecord(
        name=logger.name,
        level=logging.INFO,
        fn=__file__,
        lno=123,
        msg=msg,
        args=(),
        exc_info=None,
    )
    handler.emit(record)


def test_large_entry_rotate_first_direct(tmp_path):
    handler = make_handler(
        tmp_path,
        max_bytes=10,
        large_entry_behavior=LargeLogEntryBehavior.RotateFirst,
    )

    # Enable rotation for direct handler use
    handler.rotation_callback = lambda h: h.perform_rotation()

    emit_direct(handler, "X" * 100)

    assert (tmp_path / "direct.log.1").exists()


def test_large_entry_dump_silently_direct(tmp_path):
    handler = make_handler(
        tmp_path,
        max_bytes=10,
        large_entry_behavior=LargeLogEntryBehavior.DumpSilently,
    )

    emit_direct(handler, "X" * 100)

    assert (tmp_path / "direct.log").read_text() == ""


def test_large_entry_crash_direct(tmp_path):
    handler = make_handler(
        tmp_path,
        max_bytes=10,
        large_entry_behavior=LargeLogEntryBehavior.Crash,
    )

    with pytest.raises(ValueError):
        emit_direct(handler, "X" * 100)


def test_daily_rollover_direct(tmp_path, monkeypatch):
    handler = make_handler(
        tmp_path,
        when=When.EVERYDAY,
        timestamp=RotationTimestamp(0, 0, 0),
    )

    # Enable rotation for direct handler use
    handler.rotation_callback = lambda h: h.perform_rotation()

    monkeypatch.setattr(time, "time", lambda: 100000.0)
    handler._Async_TimedSizedRotatingFileHandler__rollover_at = 99999.0

    emit_direct(handler, "daily")
    assert (tmp_path / "direct.log.1").exists()


def test_weekly_rollover_direct(tmp_path, monkeypatch):
    handler = make_handler(
        tmp_path,
        when=When.MONDAY,
        timestamp=RotationTimestamp(0, 0, 0),
    )

    # Enable rotation for direct handler use
    handler.rotation_callback = lambda h: h.perform_rotation()

    monkeypatch.setattr(time, "time", lambda: 200000.0)
    handler._Async_TimedSizedRotatingFileHandler__rollover_at = 199000.0

    emit_direct(handler, "weekly")
    assert (tmp_path / "direct.log.1").exists()


def test_expiration_policy_direct(tmp_path, monkeypatch):
    old_file = tmp_path / "direct.log.1"
    new_file = tmp_path / "direct.log.2"
    old_file.write_text("old")
    new_file.write_text("new")

    two_days_ago = time.time() - 2 * 86400
    os.utime(old_file, (two_days_ago, two_days_ago))

    handler = make_handler(
        tmp_path,
        expiration_rule=ExpirationRule(ExpirationScale.Days, interval=1),
    )

    monkeypatch.setattr(
        handler,
        "_Async_TimedSizedRotatingFileHandler__list_rotated_files",
        lambda: [str(old_file), str(new_file)],
    )

    # noinspection PyUnresolvedReferences
    handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy()

    assert not old_file.exists()
    assert new_file.exists()


def test_rotation_callback_flag_resets_direct(tmp_path):
    calls = []

    def cb(h):
        calls.append("called")

    handler = make_handler(tmp_path, max_bytes=10)
    handler.rotation_callback = cb

    emit_direct(handler, "X" * 50)
    assert calls == ["called"]

    handler.perform_rotation()
    emit_direct(handler, "X" * 50)
    assert calls == ["called", "called"]
