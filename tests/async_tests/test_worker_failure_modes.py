import pytest
from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic


# ------------------------------------------------------------
# 1. Worker survives exceptions inside __process_log
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_worker_survives_handler_exception(tmp_path, monkeypatch):
    logger = AsyncSmartLogger("fail1")
    logger.add_file(log_dir=str(tmp_path), logfile_name="x.log")

    # Patch handler.emit to raise
    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(handler, "emit", boom)

    # This should NOT kill the worker
    await logger.a_info("hello")

    # Worker should still process further logs
    await logger.a_info("world")
    await logger.flush()

    await logger.shutdown()


# ------------------------------------------------------------
# 2. Worker survives exceptions inside rotation
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_worker_survives_rotation_exception(tmp_path, monkeypatch):
    logger = AsyncSmartLogger("fail2")

    logic = RotationLogic(maxBytes=1)
    logger.add_file(log_dir=str(tmp_path), logfile_name="x.log", rotation_logic=logic)

    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    # Patch perform_rotation to raise
    def boom():
        raise RuntimeError("rotation fail")

    monkeypatch.setattr(handler, "perform_rotation", boom)

    # Force rotation
    await logger.a_info("123456789")
    await logger.flush()

    # Worker should still be alive
    await logger.a_info("still alive")
    await logger.flush()

    await logger.shutdown()


# ------------------------------------------------------------
# 3. Queue backpressure: worker must drain queue
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_backpressure(tmp_path):
    logger = AsyncSmartLogger("fail3")
    logger.add_file(log_dir=str(tmp_path), logfile_name="x.log")

    # Enqueue many messages quickly
    for i in range(2000):
        await logger.a_info(f"msg {i}")

    # flush must drain everything
    await logger.flush()

    await logger.shutdown()


# ------------------------------------------------------------
# 4. Rotation scheduled after shutdown is ignored
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_rotation_after_shutdown_ignored(tmp_path):
    logger = AsyncSmartLogger("fail4")

    logic = RotationLogic(maxBytes=1)
    logger.add_file(log_dir=str(tmp_path), logfile_name="x.log", rotation_logic=logic)

    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    await logger.shutdown()

    # This should not crash
    logger._AsyncSmartLogger__enqueue_rotation(handler)


# ------------------------------------------------------------
# 5. Rotation scheduled after loop closed is ignored
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_rotation_after_loop_closed(tmp_path, monkeypatch):
    logger = AsyncSmartLogger("fail5")

    logic = RotationLogic(maxBytes=1)
    logger.add_file(log_dir=str(tmp_path), logfile_name="x.log", rotation_logic=logic)

    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    # Simulate closed loop
    monkeypatch.setattr(logger, "_AsyncSmartLogger__loop", None)

    # Should not crash
    logger._AsyncSmartLogger__enqueue_rotation(handler)

    await logger.shutdown()


# ------------------------------------------------------------
# 6. Worker starts lazily when no loop existed at init
# ------------------------------------------------------------
import asyncio
import logging
import pytest
from LogSmith.async_smartlogger import AsyncSmartLogger


@pytest.mark.asyncio
async def test_lazy_worker_start(tmp_path, monkeypatch):
    # Save real function
    real_get_running_loop = asyncio.get_running_loop

    # Force constructor to think there is NO running loop
    def fake_get_running_loop():
        raise RuntimeError("no loop")

    monkeypatch.setattr(asyncio, "get_running_loop", fake_get_running_loop)

    # Construct logger while "no loop" is visible
    lg = AsyncSmartLogger("lazy")

    # Restore real get_running_loop BEFORE any awaited call
    monkeypatch.setattr(asyncio, "get_running_loop", real_get_running_loop)

    # Because constructor saw "no loop", worker must NOT exist yet
    assert lg._AsyncSmartLogger__worker_tasks is None

    # Add a file handler
    lg.add_file(log_dir=str(tmp_path), logfile_name="x.log")

    # First awaited log call should start the worker
    await lg.a_info("hello")

    # Now worker must exist
    assert lg._AsyncSmartLogger__worker_tasks is not None

    await lg.shutdown()


# ------------------------------------------------------------
# 7. Worker survives exceptions inside __process_raw
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_worker_survives_raw_exception(tmp_path, monkeypatch):
    logger = AsyncSmartLogger("fail6")
    logger.add_file(log_dir=str(tmp_path), logfile_name="x.log")

    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    def boom(*args, **kwargs):
        raise RuntimeError("raw fail")

    monkeypatch.setattr(handler.stream, "write", boom)

    # Should not kill worker
    await logger.a_raw("hello")
    await logger.flush()

    await logger.shutdown()
