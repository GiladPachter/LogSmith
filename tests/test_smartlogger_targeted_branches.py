import logging
import pytest

from LogSmith import SmartLogger, LargeLogEntryBehavior, ExpirationRule, ExpirationScale
from LogSmith import LogRecordDetails
from LogSmith import RotationLogic
from LogSmith.level_registry import reset_levels_for_tests

from tests.helpers import isolated_logger


@pytest.fixture(autouse=True)
def cleanup():
    SmartLogger.terminate_auditing()
    reset_levels_for_tests()
    yield
    SmartLogger.terminate_auditing()
    reset_levels_for_tests()


# ============================================================
# 1. ANSI BLEACH EDGE CASES
# ============================================================

def test_bleach_interleaved_colors(capsys):
    logger = isolated_logger("bleach_test")
    logger.add_console()

    msg = "plain \x1b[31mred\x1b[0m plain"
    logger.raw(msg)

    out = capsys.readouterr().out
    assert "red" in out
    assert "plain" in out


# ============================================================
# 2. RAW() SKIP HANDLER BRANCH
# ============================================================

def test_raw_skips_handler_with_no_stream():
    logger = isolated_logger("raw_skip")

    class Dummy(logging.Handler):
        stream = None

    dummy = Dummy()
    logger._SmartLogger__py_logger.addHandler(dummy)

    # Should not crash, should skip dummy handler
    logger.raw("hello")


# ============================================================
# 3. RETIRE / DESTROY GUARD RAILS + REENTRANCY
# ============================================================

def test_retire_destroy_reentrant(tmp_path):
    logger = isolated_logger("life_test")
    logger.add_console()

    logger.retire()

    with pytest.raises(Exception):
        logger.info("x")

    logger.destroy()
    logger.destroy()  # reentrant

    for op in [
        lambda: logger.info("x"),
        lambda: logger.raw("x"),
        lambda: logger.add_console(),
        lambda: logger.add_file(log_dir=str(tmp_path), logfile_name="x.log"),
        lambda: logger.remove_console(),
        lambda: logger.remove_file_handler("x.log", str(tmp_path)),
    ]:
        with pytest.raises(Exception):
            op()


# ============================================================
# 4. REMOVE HANDLER CLEANUP
# ============================================================

def test_remove_console_cleanup():
    logger = isolated_logger("rm_console")
    logger.add_console()
    assert logger.console_handler is not None

    logger.remove_console()
    assert logger.console_handler is None


def test_remove_file_handler_cleanup(tmp_path):
    logger = isolated_logger("rm_file")
    log_dir = tmp_path / "rm"
    log_dir.mkdir()

    logger.add_file(log_dir=str(log_dir), logfile_name="x.log")
    assert len(logger.file_handlers) == 1

    logger.remove_file_handler("x.log", str(log_dir))
    assert len(logger.file_handlers) == 0

    logger.destroy()


# ============================================================
# 5. GET_RECORD EDGE CASES
# ============================================================

def test_get_record_exc_and_stack():
    try:
        1 / 0
    except ZeroDivisionError:
        rec = SmartLogger.get_record()
        assert rec.exc_info is not None

    lg = SmartLogger("stack_test")
    lg.add_console()
    lg.debug("stack", stack_info=True)
    rec2 = SmartLogger.get_record()
    assert rec2.stack_info is not None


# ============================================================
# 6. AUDIT HANDLER INFO EDGE CASES
# ============================================================

def test_audit_handler_info_edges(tmp_path):
    log_dir = tmp_path / "audit"
    log_dir.mkdir()

    details = LogRecordDetails()
    SmartLogger.audit_everything(
        log_dir=str(log_dir),
        logfile_name="a.log",
        rotation_logic=None,
        details=details,
    )

    info = SmartLogger.audit_handler_info()
    assert info is not None
    assert info["rotation"] is None  # audit does not expose rotation metadata

    SmartLogger.terminate_auditing()
    assert SmartLogger.audit_handler_info() is None


# ============================================================
# 7. HANDLER METADATA (console/file/output_targets)
# ============================================================

def test_handler_metadata(tmp_path):
    logger = isolated_logger("meta_test")

    logger.add_console()
    assert logger.console_handler["kind"] == "console"

    log_dir = tmp_path / "meta"
    log_dir.mkdir()
    logger.add_file(log_dir=str(log_dir), logfile_name="x.log")

    assert len(logger.file_handlers) == 1
    assert "console" in logger.output_targets
    assert any("x.log" in p for p in logger.output_targets)

    logger.destroy()


# ============================================================
# 8. ROTATION LOGIC RARE BRANCHES
# ============================================================

def test_rotation_logic_timestamp(tmp_path):
    import datetime
    from LogSmith.rotation_base import RotationTimestamp

    logger = isolated_logger("rot_ts")
    log_dir = tmp_path / "ts"
    log_dir.mkdir()

    # Compute a timestamp 2 seconds in the future
    future = datetime.datetime.now() + datetime.timedelta(seconds=2)
    ts = RotationTimestamp(
        hour=future.hour,
        minute=future.minute,
        second=future.second,
    )

    rot = RotationLogic(timestamp=ts)

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="x.log",
        rotation_logic=rot,
    )

    info = logger.file_handlers[0]["rotation"]

    # Timestamp-only rotation → when=None, interval=None, maxBytes=None
    assert info["when"] is None
    assert info["interval"] is None
    assert info["maxBytes"] is None

    logger.destroy()


def test_rotation_logic_expiration(tmp_path):
    logger = isolated_logger("rot_exp")
    log_dir = tmp_path / "exp"
    log_dir.mkdir()

    rot = RotationLogic(expiration_rule=ExpirationRule(ExpirationScale.Days, interval=7))
    logger.add_file(log_dir=str(log_dir), logfile_name="x.log", rotation_logic=rot)

    info = logger.file_handlers[0]["rotation"]
    assert info["backupCount"] == 5  # default

    logger.destroy()


def test_rotation_logic_large_entry(tmp_path):
    logger = isolated_logger("rot_large")
    log_dir = tmp_path / "large"
    log_dir.mkdir()

    rot = RotationLogic(log_entry_larger_than_maxBytes_behavior=LargeLogEntryBehavior.DumpSilently)
    logger.add_file(log_dir=str(log_dir), logfile_name="x.log", rotation_logic=rot)

    info = logger.file_handlers[0]["rotation"]
    assert info["maxBytes"] is None

    logger.destroy()


# ============================================================
# 9. LEVEL REGISTRY SAFEGUARD
# ============================================================

def test_level_registry_safeguard():
    with pytest.raises(Exception):
        SmartLogger.register_level("INFO", 20)  # duplicate name

    with pytest.raises(Exception):
        SmartLogger.register_level("BAD NAME!", 55)


# ============================================================
# 10. INVALID THEME REGISTRATION
# ============================================================

def test_invalid_theme_registration():
    with pytest.raises(Exception):
        SmartLogger.apply_color_theme({20: "not a LevelStyle"})
