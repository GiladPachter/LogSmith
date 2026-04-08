import pytest

from LogSmith import SmartLogger
from LogSmith import AsyncSmartLogger
from LogSmith import RotationLogic
from LogSmith import CPrint


def test_smartlogger_audit_sanitizes_colors(tmp_path):
    logdir = tmp_path
    audit_file = logdir / "audit.log"

    SmartLogger.audit_everything(
        log_dir=str(logdir),
        logfile_name="audit.log",
        rotation_logic=RotationLogic(),
    )

    lg = SmartLogger("audit_test_smart")

    colored = CPrint.colorize("HELLO", fg=CPrint.FG.RED)

    lg.info(colored)

    for h in lg._SmartLogger__py_logger.handlers:
        h.flush()

    text = audit_file.read_text()

    # ANSI should NOT be present
    assert "\x1b[" not in text
    # Message should be present
    assert "HELLO" in text

    SmartLogger.terminate_auditing()
    lg.destroy()


@pytest.mark.asyncio
async def test_asyncsmartlogger_audit_sanitizes_colors(tmp_path):
    await AsyncSmartLogger.terminate_auditing()  # ensure clean state

    logdir = tmp_path
    audit_file = logdir / "audit.log"

    await AsyncSmartLogger.audit_everything(
        log_dir=str(logdir),
        logfile_name="audit.log",
        rotation_logic=RotationLogic(),
    )

    lg = AsyncSmartLogger("audit_test_async_sanitized")

    colored = CPrint.colorize("HELLO", fg=CPrint.FG.GREEN)

    await lg.a_info(colored)
    await lg.flush()

    # Flush the audit logger too
    await AsyncSmartLogger._AsyncSmartLogger__audit_logger.flush()

    text = audit_file.read_text()

    assert "\x1b[" not in text
    assert "HELLO" in text

    await AsyncSmartLogger.terminate_auditing()
    await lg.shutdown()
    lg.destroy()


def test_smartlogger_audit_preserves_colors(tmp_path):
    logdir = tmp_path
    audit_file = logdir / "audit.log"

    # Enable auditing
    SmartLogger.audit_everything(
        log_dir=str(logdir),
        logfile_name="audit.log",
        rotation_logic=RotationLogic(),
    )

    lg = SmartLogger("audit_test_smart")

    # Add a file handler that DISABLES sanitization
    lg.add_file(
        log_dir=str(logdir),
        logfile_name="dummy.log",
        preserve_colors_in_log_files=True,
    )

    colored = CPrint.colorize("HELLO", fg=CPrint.FG.RED)

    lg.info(colored)

    # Flush handlers
    for h in lg._SmartLogger__py_logger.handlers:
        h.flush()

    text = audit_file.read_text()

    # ANSI must be present
    assert "\x1b[" in text
    assert "HELLO" in text

    SmartLogger.terminate_auditing()
    lg.destroy()


@pytest.mark.asyncio
async def test_asyncsmartlogger_audit_preserves_colors(tmp_path):
    await AsyncSmartLogger.terminate_auditing()  # ensure clean state

    logdir = tmp_path
    audit_file = logdir / "audit.log"

    await AsyncSmartLogger.audit_everything(
        log_dir=str(logdir),
        logfile_name="audit.log",
        rotation_logic=RotationLogic(),
    )

    lg = AsyncSmartLogger("audit_test_async_preserve")

    # Add a file handler that disables sanitization
    lg.add_file(
        log_dir=str(logdir),
        logfile_name="dummy.log",
        preserve_colors_in_log_files=True,
    )

    colored = CPrint.colorize("HELLO", fg=CPrint.FG.GREEN)

    await lg.a_info(colored)
    await lg.flush()

    # Flush the audit logger too
    await AsyncSmartLogger._AsyncSmartLogger__audit_logger.flush()

    text = audit_file.read_text()

    assert "\x1b[" in text
    assert "HELLO" in text

    await AsyncSmartLogger.terminate_auditing()
    await lg.shutdown()
    lg.destroy()
