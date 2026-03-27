import pytest
from pathlib import Path
from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic


# ------------------------------------------------------------
# 1. Adding multiple file handlers works
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_multiple_file_handlers(tmp_path):
    logger = AsyncSmartLogger("multi")

    logger.add_file(log_dir=str(tmp_path), logfile_name="a.log")
    logger.add_file(log_dir=str(tmp_path), logfile_name="b.log")

    handlers = logger._AsyncSmartLogger__py_logger.handlers
    assert len(handlers) == 2

    await logger.shutdown()


# ------------------------------------------------------------
# 2. Handlers do not interfere with each other
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_handlers_independent(tmp_path):
    logger = AsyncSmartLogger("independent")

    logger.add_file(log_dir=str(tmp_path), logfile_name="x.log")
    logger.add_file(log_dir=str(tmp_path), logfile_name="y.log")

    await logger.a_info("hello")
    await logger.flush()

    for h in logger._AsyncSmartLogger__py_logger.handlers:
        text = Path(h.baseFilename).read_text()
        assert "hello" in text

    await logger.shutdown()


# ------------------------------------------------------------
# 3. Rotation does not break handler references
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_rotation_handler_survives(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "LogSmith.async_rotation.Async_TimedSizedRotatingFileHandler._rotation_suffix",
        lambda self: "ROT"
    )

    logic = RotationLogic(
        when=None,
        maxBytes=10,
        backupCount=1,
    )

    logger = AsyncSmartLogger("rotate")
    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="rot.log",
        rotation_logic=logic,
    )

    await logger.a_info("1234567890")
    await logger.flush()

    handlers = logger._AsyncSmartLogger__py_logger.handlers
    assert len(handlers) == 1

    await logger.shutdown()


# ------------------------------------------------------------
# 4. Shutdown closes all handlers
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_shutdown_closes_handlers(tmp_path):
    logger = AsyncSmartLogger("shutdown")

    logger.add_file(log_dir=str(tmp_path), logfile_name="s1.log")
    logger.add_file(log_dir=str(tmp_path), logfile_name="s2.log")

    handlers = logger._AsyncSmartLogger__py_logger.handlers

    await logger.shutdown()

    for h in handlers:
        assert h.stream is None or h.stream.closed


# ------------------------------------------------------------
# 5. Audit termination closes audit handler
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_termination_clears_handler(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit_test.log",
    )

    handler = AsyncSmartLogger._AsyncSmartLogger__audit_handler
    assert handler is not None

    await AsyncSmartLogger.terminate_auditing()

    # The handler reference must be cleared
    assert AsyncSmartLogger._AsyncSmartLogger__audit_handler is None

    # The handler object still exists, but is no longer used
    assert handler.stream is not None
    assert not handler.stream.closed


# ------------------------------------------------------------
# 6. No global state leaks between loggers
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_no_global_state_leak(tmp_path):
    logger1 = AsyncSmartLogger("L1")
    logger2 = AsyncSmartLogger("L2")

    logger1.add_file(log_dir=str(tmp_path), logfile_name="l1.log")
    logger2.add_file(log_dir=str(tmp_path), logfile_name="l2.log")

    assert logger1._AsyncSmartLogger__py_logger is not logger2._AsyncSmartLogger__py_logger

    await logger1.shutdown()
    await logger2.shutdown()
