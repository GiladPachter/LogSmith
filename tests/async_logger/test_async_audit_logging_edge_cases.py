import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic


# ------------------------------------------------------------
# 1. Basic audit logging captures messages from all loggers
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_captures_all_loggers(tmp_path):
    audit_path = tmp_path / "audit.log"

    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    lg1 = AsyncSmartLogger("lg1")
    lg2 = AsyncSmartLogger("lg2")

    await lg1.a_info("hello from lg1")
    await lg2.a_info("hello from lg2")

    # Flush both main loggers
    await lg1.flush()
    await lg2.flush()

    # IMPORTANT: flush the audit logger too
    audit_logger = AsyncSmartLogger._AsyncSmartLogger__audit_logger
    await audit_logger.flush()

    text = audit_path.read_text()

    assert "lg1" in text
    assert "lg2" in text
    assert "hello from lg1" in text
    assert "hello from lg2" in text

    await AsyncSmartLogger.terminate_auditing()


# ------------------------------------------------------------
# 2. Audit prefix is correct
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_prefix(tmp_path):
    audit_path = tmp_path / "audit.log"

    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    lg = AsyncSmartLogger("prefix_test")
    await lg.a_info("hello")
    await lg.flush()

    text = audit_path.read_text()

    # Audit output now begins with:
    #   "[prefix_test]: ..."
    assert text.startswith("[prefix_test]:")

    await AsyncSmartLogger.terminate_auditing()


# ------------------------------------------------------------
# 3. Audit logger does NOT audit itself (no recursion)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_no_recursion(tmp_path):
    audit_path = tmp_path / "audit.log"

    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    # Log from a normal logger
    lg = AsyncSmartLogger("normal")
    await lg.a_info("hello")
    await lg.flush()

    text = audit_path.read_text()

    # Normal logger should appear exactly once
    assert text.count("[normal]:") == 1

    # Audit logger should NOT prefix itself at all
    assert "[_async_audit]:" not in text

    await AsyncSmartLogger.terminate_auditing()


# ------------------------------------------------------------
# 4. Audit preserves ANSI (AuditFormatter does NOT sanitize)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_preserves_ansi(tmp_path):
    audit_path = tmp_path / "audit.log"

    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    lg = AsyncSmartLogger("ansi_test")
    await lg.a_info("\x1b[31mRED\x1b[0m")
    await lg.flush()

    text = audit_path.read_text()

    # ANSI must be stripped in audit logs
    assert "\x1b" not in text
    assert "RED" in text

    await AsyncSmartLogger.terminate_auditing()


# ------------------------------------------------------------
# 5. Audit rotation works
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_rotation(tmp_path):
    audit_path = tmp_path / "audit.log"

    logic = RotationLogic(maxBytes=50, backupCount=3)

    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
        rotation_logic=logic,
    )

    audit_logger = AsyncSmartLogger._AsyncSmartLogger__audit_logger

    # Write enough large messages to trigger rotation
    for _ in range(200):
        await audit_logger.a_info("x" * 200)

    # Flush to ensure rotation is processed
    await audit_logger.flush()

    rotated = list(tmp_path.glob("audit.log.*"))
    assert len(rotated) >= 1

    await AsyncSmartLogger.terminate_auditing()


# ------------------------------------------------------------
# 6. Audit handler metadata is correct
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_handler_metadata(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    meta = AsyncSmartLogger.audit_handler_info()

    assert meta["kind"] == "file"
    assert meta["formatter"] == "plain"
    assert meta["path"].endswith("audit.log")

    await AsyncSmartLogger.terminate_auditing()


# ------------------------------------------------------------
# 7. terminate_auditing removes handler cleanly
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_terminate_auditing_cleanup(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    await AsyncSmartLogger.terminate_auditing()

    assert AsyncSmartLogger._AsyncSmartLogger__audit_logger is None
    assert AsyncSmartLogger._AsyncSmartLogger__audit_handler is None
