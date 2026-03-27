import pytest
from pathlib import Path

from LogSmith import SmartLogger
from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.file_registry import FileHandlerRegistry
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


# ------------------------------------------------------------
# 7. Basic register/unregister
# ------------------------------------------------------------
def test_basic_register_unregister(tmp_path):
    p = tmp_path / "a.log"

    FileHandlerRegistry.register(str(p))
    # noinspection PyUnresolvedReferences
    assert str(p.resolve()) in FileHandlerRegistry._FileHandlerRegistry__active_paths

    FileHandlerRegistry.unregister(str(p))
    # noinspection PyUnresolvedReferences
    assert str(p.resolve()) not in FileHandlerRegistry._FileHandlerRegistry__active_paths


# ------------------------------------------------------------
# 8. Duplicate registration raises
# ------------------------------------------------------------
def test_duplicate_registration_raises(tmp_path):
    p = tmp_path / "dup.log"

    FileHandlerRegistry.register(str(p))
    with pytest.raises(ValueError):
        FileHandlerRegistry.register(str(p))

    FileHandlerRegistry.unregister(str(p))


# ------------------------------------------------------------
# 9. Normalization: different string → same resolved path
# ------------------------------------------------------------
def test_normalization(tmp_path):
    p1 = tmp_path / "norm.log"
    p2 = Path(str(tmp_path)) / "./norm.log"

    FileHandlerRegistry.register(str(p1))
    with pytest.raises(ValueError):
        FileHandlerRegistry.register(str(p2))

    FileHandlerRegistry.unregister(str(p1))


# ------------------------------------------------------------
# 10. SmartLogger respects registry
# ------------------------------------------------------------
def test_smartlogger_respects_registry(tmp_path):
    p = tmp_path / "s.log"

    lg1 = SmartLogger("s1")
    lg1.add_file(log_dir=str(tmp_path), logfile_name="s.log")

    lg2 = SmartLogger("s2")
    with pytest.raises(ValueError):
        lg2.add_file(log_dir=str(tmp_path), logfile_name="s.log")

    lg1.destroy()
    FileHandlerRegistry.unregister(str(p))


# ------------------------------------------------------------
# 11. AsyncSmartLogger respects registry
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_asyncsmartlogger_respects_registry(tmp_path):
    p = tmp_path / "a.log"

    lg1 = AsyncSmartLogger("a1")
    lg1.add_file(log_dir=str(tmp_path), logfile_name="a.log")

    lg2 = AsyncSmartLogger("a2")
    with pytest.raises(ValueError):
        lg2.add_file(log_dir=str(tmp_path), logfile_name="a.log")

    await lg1.shutdown()
    FileHandlerRegistry.unregister(str(p))


# ------------------------------------------------------------
# 12. Removing handler cleans registry
# ------------------------------------------------------------
def test_remove_handler_cleans_registry(tmp_path):
    p = tmp_path / "clean.log"

    lg = SmartLogger("clean")
    lg.add_file(log_dir=str(tmp_path), logfile_name="clean.log")

    # noinspection PyUnresolvedReferences
    assert str(p.resolve()) in FileHandlerRegistry._FileHandlerRegistry__active_paths

    lg.remove_file_handler("clean.log", str(tmp_path))

    # noinspection PyUnresolvedReferences
    assert str(p.resolve()) not in FileHandlerRegistry._FileHandlerRegistry__active_paths

    lg.destroy()


# ------------------------------------------------------------
# 13. Async remove handler cleans registry
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_async_remove_handler_cleans_registry(tmp_path):
    p = tmp_path / "clean_async.log"

    lg = AsyncSmartLogger("clean_async")
    lg.add_file(log_dir=str(tmp_path), logfile_name="clean_async.log")

    # noinspection PyUnresolvedReferences
    assert str(p.resolve()) in FileHandlerRegistry._FileHandlerRegistry__active_paths

    lg.remove_file_handler("clean_async.log", str(tmp_path))

    # noinspection PyUnresolvedReferences
    assert str(p.resolve()) not in FileHandlerRegistry._FileHandlerRegistry__active_paths

    await lg.shutdown()
