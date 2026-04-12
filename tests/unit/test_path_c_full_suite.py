# tests/test_path_c_full_suite.py
import asyncio
import logging
import os
import time

import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic, ExpirationRule, ExpirationScale
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.smartlogger import SmartLogger
from LogSmith.rotation import ConcurrentTimedSizedRotatingFileHandler


# ---------------------------------------------------------------------------
# Async rotation + expiration (through AsyncSmartLogger)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_expiration_policy_on_existing_rotated_files(tmp_path):
    import os, time
    from datetime import datetime, timedelta
    from LogSmith.async_smartlogger import AsyncSmartLogger
    from LogSmith.rotation_base import RotationLogic, ExpirationRule, ExpirationScale
    from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler

    # Manually create a handler pointing at tmp_path/exp.log
    rotation = RotationLogic(
        maxBytes=1,
        backupCount=5,
        expiration_rule=ExpirationRule(
            scale=ExpirationScale.Seconds,
            interval=1,
        ),
    )

    lg = AsyncSmartLogger("expiration_unit_test")
    lg.add_file(str(tmp_path), "exp.log", rotation_logic=rotation)

    handler: Async_TimedSizedRotatingFileHandler = next(
        h for h in lg._AsyncSmartLogger__py_logger.handlers
        if isinstance(h, Async_TimedSizedRotatingFileHandler)
    )

    # Create fake rotated files
    paths = [
        tmp_path / "exp.log.1",
        tmp_path / "exp.log.2",
        tmp_path / "exp.log.3",
    ]
    for p in paths:
        p.write_text("x")

    very_old = time.time() - 999999
    for p in paths:
        os.utime(p, (very_old, very_old))

    # Call expiration directly in a thread, under the handler lock
    with handler.write_lock:
        await asyncio.to_thread(handler._Async_TimedSizedRotatingFileHandler__apply_expiration_policy)

    # All should be gone
    for p in paths:
        assert not p.exists()


# ---------------------------------------------------------------------------
# AsyncSmartLogger: RAW / console-only behavior
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_async_logger_raw_console_only_does_not_touch_file(tmp_path, capsys):
    """
    a_stdout() should enqueue a console-only RAW operation:
    - console handler receives output
    - file handler does NOT receive output
    """
    lg = AsyncSmartLogger("async_raw_console_only")

    # Attach console handler
    lg.add_console()

    # Attach file handler
    rotation = RotationLogic(maxBytes=0)
    lg.add_file(str(tmp_path), "raw.log", rotation_logic=rotation)

    # Use a_stdout (console-only)
    await lg.a_stdout("hello-console-only")
    await lg.flush()

    # File should exist but be empty (no RAW written there)
    file_path = tmp_path / "raw.log"
    assert file_path.exists()
    assert file_path.read_text() == ""


# ---------------------------------------------------------------------------
# AsyncSmartLogger: dynamic level registration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_async_logger_dynamic_level(tmp_path):
    """
    Register a custom level and use a_<name>() dynamically.
    """
    from LogSmith.levels import LevelStyle
    from LogSmith.level_registry import LEVELS

    # Register a new level
    name = "CUSTOMX"
    value = 45
    style = LevelStyle()
    if name not in LEVELS.all():
        AsyncSmartLogger.register_level(name, value, style)

    lg = AsyncSmartLogger("async_dynamic_level")
    lg.add_file(str(tmp_path), "dyn.log", rotation_logic=RotationLogic(maxBytes=0))

    # Call a_CUSTOMX dynamically
    method = getattr(lg, "a_customx")
    await method("dynamic-level-message")
    await lg.flush()

    text = (tmp_path / "dyn.log").read_text()
    assert "dynamic-level-message" in text


# ---------------------------------------------------------------------------
# SmartLogger: duplicate console handler detection
# ---------------------------------------------------------------------------

def test_smartlogger_duplicate_console():
    """
    SmartLogger.add_console() should reject a second console handler.
    """
    lg = SmartLogger("smart_dup_console")
    lg.add_console()

    with pytest.raises(RuntimeError):
        lg.add_console()


# ---------------------------------------------------------------------------
# SmartLogger: duplicate file handler detection (process-wide)
# ---------------------------------------------------------------------------

def test_smartlogger_duplicate_file_handler(tmp_path):
    """
    SmartLogger.add_file() should reject a second file handler pointing
    to the same resolved path, even across different SmartLogger instances.
    """
    log_dir = str(tmp_path.resolve())
    logfile = "dup.log"

    lg1 = SmartLogger("smart_dup_file_1")
    lg1.add_file(log_dir=log_dir, logfile_name=logfile, rotation_logic=RotationLogic(maxBytes=0))

    lg2 = SmartLogger("smart_dup_file_2")
    with pytest.raises(ValueError):
        lg2.add_file(log_dir=log_dir, logfile_name=logfile, rotation_logic=RotationLogic(maxBytes=0))


# ---------------------------------------------------------------------------
# SmartLogger: stdout fallback when no console handler
# ---------------------------------------------------------------------------

def test_smartlogger_stdout_fallback_no_console(capsys):
    """
    SmartLogger.stdout() should fall back to print() when no console handler exists.
    """
    lg = SmartLogger("smart_stdout_fallback")

    lg.stdout("hello-fallback")
    captured = capsys.readouterr()
    assert "hello-fallback" in captured.out


# ---------------------------------------------------------------------------
# SmartLogger: raw() with no handlers should raise on retired logger
# ---------------------------------------------------------------------------

def test_smartlogger_raw_on_retired_logger(tmp_path):
    """
    raw() on a retired logger should raise RuntimeError.
    """
    lg = SmartLogger("smart_raw_retired")
    lg.add_file(log_dir=str(tmp_path.resolve()), logfile_name="x.log", rotation_logic=RotationLogic(maxBytes=0))

    lg.retire()
    with pytest.raises(RuntimeError):
        lg.raw(logging.INFO, "should-fail")


# ---------------------------------------------------------------------------
# Sync rotation: size-based rotation without expiration
# ---------------------------------------------------------------------------

def test_sync_rotation_size_no_expiration(tmp_path):
    """
    ConcurrentTimedSizedRotatingFileHandler should rotate on size even when
    no expiration_rule is provided.
    """
    log_path = tmp_path / "sync.log"

    rotation = RotationLogic(maxBytes=1)  # force rotation on second write
    handler = ConcurrentTimedSizedRotatingFileHandler(
        filename=str(log_path),
        when=rotation.when,
        interval=rotation.interval or 1,
        timestamp=rotation.timestamp,
        max_bytes=rotation.maxBytes or 0,
        backup_count=rotation.backupCount,
        expiration_rule=rotation.expiration_rule,
        encoding="utf-8",
        large_entry_behavior=rotation.large_entry_behavior,
        append_filename_pid=rotation.append_filename_pid,
        append_filename_timestamp=rotation.append_filename_timestamp,
    )

    logger = logging.getLogger("sync.rotation.no.expiration")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info("A")
    logger.info("B")

    handler.flush()
    logger.removeHandler(handler)
    handler.close()

    # Base file and first rotated file should exist
    assert log_path.exists()
    rotated = tmp_path / "sync.log.1"
    assert rotated.exists()


# ---------------------------------------------------------------------------
# Async rotation: handler used directly (no rotation callback)
# ---------------------------------------------------------------------------

def test_async_rotation_emit_direct_does_not_rotate(tmp_path):
    """
    Calling Async_TimedSizedRotatingFileHandler.emit() directly is not a valid
    usage path for AsyncSmartLogger. It should not trigger rotation.
    """
    log_path = tmp_path / "direct.log"

    handler = Async_TimedSizedRotatingFileHandler(
        filename=str(log_path),
        when=None,
        interval=1,
        timestamp=None,
        max_bytes=1,
        backup_count=1,
        expiration_rule=None,
        encoding="utf-8",
        large_entry_behavior=None,
        append_filename_pid=False,
        append_filename_timestamp=False,
        audit_mode=False,
    )

    record1 = logging.LogRecord("x", logging.INFO, __file__, 1, "A", (), None)
    record2 = logging.LogRecord("x", logging.INFO, __file__, 1, "B", (), None)

    handler.emit(record1)
    handler.emit(record2)
    handler.flush()
    handler.close()

    # No rotation callback was wired, so no rotation should have occurred
    assert log_path.exists()
    rotated = tmp_path / "direct.log.1"
    assert not rotated.exists()
