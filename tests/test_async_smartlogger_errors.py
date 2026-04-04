import logging
import os
import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic, When


# ------------------------------------------------------------
# 1. Worker swallows handler.emit exceptions (REAL LogSmith branch)
# ------------------------------------------------------------

class ExplodingHandler(logging.Handler):
    def emit(self, record):
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_handler_emit_failure_is_swallowed(tmp_path):
    logger = AsyncSmartLogger("explode-test")
    logger._AsyncSmartLogger__py_logger.addHandler(ExplodingHandler())

    # Should not crash
    await logger.a_info("msg")
    await logger.flush()

    # Worker should still be alive
    for t in logger._AsyncSmartLogger__worker_tasks:
        assert not t.done()


# ------------------------------------------------------------
# 2. Stream write failure path (REAL LogSmith branch)
# ------------------------------------------------------------

class FakeStream:
    def write(self, _):
        raise IOError("write failed")

    def flush(self):
        raise IOError("flush failed")


@pytest.mark.asyncio
async def test_stream_write_failure_is_swallowed(tmp_path):
    logger = AsyncSmartLogger("streamfail")
    log_dir = os.path.abspath(tmp_path.as_posix())
    logger.add_file(log_dir, "streamfail.log")

    handler = logger._AsyncSmartLogger__py_logger.handlers[-1]

    # Break stream for worker write
    original_stream = handler.stream
    handler.stream = FakeStream()

    await logger.a_info("msg")

    # Restore valid stream before flush()
    handler.stream = original_stream

    await logger.flush()  # now safe


# ------------------------------------------------------------
# 3. Stream reopen logic (stream=None)
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_stream_reopen_logic(tmp_path):
    logger = AsyncSmartLogger("reopen")
    log_dir = os.path.abspath(tmp_path.as_posix())
    logger.add_file(log_dir, "reopen.log")

    handler = logger._AsyncSmartLogger__py_logger.handlers[-1]
    handler.stream.close()
    handler.stream = None

    await logger.a_info("hello")
    await logger.flush()

    text = (tmp_path / "reopen.log").read_text()
    assert "hello" in text


# ------------------------------------------------------------
# 4. Rotation callback failure path
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_rotation_callback_failure_is_swallowed(tmp_path):
    logger = AsyncSmartLogger("rotfail")
    log_dir = os.path.abspath(tmp_path.as_posix())

    rotation_logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        timestamp=None,
        maxBytes=5,
        backupCount=1,
        expiration_rule=None,
        log_entry_larger_than_maxBytes_behavior=None,
    )

    logger.add_file(log_dir, "rotfail.log", rotation_logic=rotation_logic)
    handler = logger._AsyncSmartLogger__py_logger.handlers[-1]

    def bad_callback(_):
        raise RuntimeError("rotation callback exploded")

    handler.rotation_callback = bad_callback

    # Should not crash
    await logger.a_info("X" * 100)
    await logger.flush()

    logger.destroy()


# ------------------------------------------------------------
# 5. RAW write failure path
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_raw_write_failure_is_swallowed(tmp_path):
    logger = AsyncSmartLogger("rawfail")
    log_dir = os.path.abspath(tmp_path.as_posix())
    logger.add_file(log_dir, "rawfail.log")

    handler = logger._AsyncSmartLogger__py_logger.handlers[-1]

    # Break stream for worker write
    original_stream = handler.stream
    handler.stream = FakeStream()

    await logger.a_raw("raw text")

    # Restore valid stream before flush()
    handler.stream = original_stream

    await logger.flush()  # now safe


# ------------------------------------------------------------
# 6. __getattr__ fallback for dynamic levels
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_getattr_dynamic_level_fallback(tmp_path):
    # Register a new level
    AsyncSmartLogger.register_level("NOTICE", 25, style=None)

    logger = AsyncSmartLogger("dyn")
    log_dir = os.path.abspath(tmp_path.as_posix())
    logger.add_file(log_dir, "dyn.log")

    # a_notice should now exist dynamically
    await logger.a_notice("hello")
    await logger.flush()

    text = (tmp_path / "dyn.log").read_text()
    assert "hello" in text

    logger.destroy()


# ------------------------------------------------------------
# 7. find_caller edge case (nested call)
# ------------------------------------------------------------

async def nested_call(logger):
    await logger.a_info("nested")


@pytest.mark.asyncio
async def test_find_caller_nested(tmp_path):
    logger = AsyncSmartLogger("caller")
    log_dir = os.path.abspath(tmp_path.as_posix())
    logger.add_file(log_dir, "caller.log")

    await nested_call(logger)
    await logger.flush()

    text = (tmp_path / "caller.log").read_text()
    assert "nested" in text

    logger.destroy()


# ------------------------------------------------------------
# 8. Profiling mode branches
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_profiling_branches(tmp_path):
    logger = AsyncSmartLogger("profile")
    logger.enable_profiling(True)

    log_dir = os.path.abspath(tmp_path.as_posix())
    logger.add_file(log_dir, "profile.log")

    for _ in range(20):
        await logger.a_info("msg")

    await logger.flush()

    details = logger.get_profiling_details()
    assert "Avg" in details


# ------------------------------------------------------------
# 9. Audit mode error paths
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_audit_mode_error_paths(tmp_path):
    log_dir = os.path.abspath(tmp_path.as_posix())

    await AsyncSmartLogger.audit_everything(
        log_dir=log_dir,
        logfile_name="audit.log",
        rotation_logic=None,
        details=None,
    )

    logger = AsyncSmartLogger("audit-test")
    logger.add_file(log_dir, "audit-test.log")

    await logger.a_info("audit message")
    await logger.flush()

    info = AsyncSmartLogger.audit_handler_info()
    assert info is not None

    await AsyncSmartLogger.terminate_auditing()
    assert AsyncSmartLogger.audit_handler_info() is None

    logger.destroy()


# ------------------------------------------------------------
# 10. Shutdown edge cases
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_shutdown_twice(tmp_path):
    logger = AsyncSmartLogger("shutdown2")
    log_dir = os.path.abspath(tmp_path.as_posix())
    logger.add_file(log_dir, "sh2.log")

    await logger.a_info("msg")
    await logger.shutdown()

    # Second shutdown should not crash
    await logger.shutdown()


# ------------------------------------------------------------
# 11. Retire then shutdown
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_retire_then_shutdown(tmp_path):
    logger = AsyncSmartLogger("retire-shut")
    log_dir = os.path.abspath(tmp_path.as_posix())
    logger.add_file(log_dir, "rs.log")

    await logger.a_info("before")
    logger.retire()

    with pytest.raises(RuntimeError):
        await logger.a_info("after")

    await logger.shutdown()


# ------------------------------------------------------------
# 12. Queue backpressure branch (qsize > 10000)
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_queue_backpressure_branch(tmp_path):
    logger = AsyncSmartLogger("backpressure")
    log_dir = os.path.abspath(tmp_path.as_posix())
    logger.add_file(log_dir, "bp.log")

    # Force qsize > 10000
    for _ in range(10050):
        await logger._AsyncSmartLogger__enqueue_log(
            level=logging.INFO,
            msg="x",
            args=(),
            extra={},
            fields={},
            exc_info=None,
            stack_info_flag=False,
            pathname=__file__,
            lineno=1,
            func_name="f",
        )

    await logger.flush()

    logger.destroy()
