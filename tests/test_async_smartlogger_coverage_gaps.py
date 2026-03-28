import asyncio
import logging
import pytest
from LogSmith.async_smartlogger import AsyncSmartLogger, AsyncOp, _QueueItem
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.rotation_base import RotationLogic


# ------------------------------------------------------------
# 1. Worker stops on SENTINEL
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_worker_stops_on_sentinel():
    lg = AsyncSmartLogger("sentinel_test")

    # Push sentinel directly
    lg._AsyncSmartLogger__queue.put_nowait(
        _QueueItem(op=AsyncOp.SENTINEL, payload={})
    )

    await asyncio.sleep(0)  # allow worker to process

    # At least one worker task should be done
    assert any(t.done() for t in lg._AsyncSmartLogger__worker_tasks)


# ------------------------------------------------------------
# 2. Worker swallows handler exceptions
# ------------------------------------------------------------
class ExplodingHandler(logging.Handler):
    def emit(self, record):
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_worker_swallows_handler_exceptions():
    lg = AsyncSmartLogger("explode_test")
    lg._AsyncSmartLogger__py_logger.addHandler(ExplodingHandler())

    # Should not raise
    await lg.a_info("hello")
    await asyncio.sleep(0)

    # Worker must still be alive
    assert all(not t.done() for t in lg._AsyncSmartLogger__worker_tasks)


# ------------------------------------------------------------
# 3. Deferred worker creation
# ------------------------------------------------------------
def test_deferred_worker_creation():
    lg = AsyncSmartLogger("deferred_test")  # created outside event loop
    assert lg._AsyncSmartLogger__worker_tasks is None

    async def use_logger():
        await lg.a_info("hello")
        assert lg._AsyncSmartLogger__worker_tasks is not None

    asyncio.run(use_logger())


# ------------------------------------------------------------
# 4. RAW stream reopening
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_raw_reopens_file(tmp_path):
    lg = AsyncSmartLogger("raw_test")
    lg.add_file(str(tmp_path), "raw.log")

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]
    handler.stream = None  # simulate missing stream

    await lg.a_raw("hello")
    await lg.flush()

    text = (tmp_path / "raw.log").read_text()
    assert "hello" in text


# ------------------------------------------------------------
# 5. Rotation callback path
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_rotation_callback(tmp_path):
    logic = RotationLogic(maxBytes=20, backupCount=2)
    lg = AsyncSmartLogger("rotate_test")
    lg.add_file(str(tmp_path), "rot.log", rotation_logic=logic)

    handler = lg._AsyncSmartLogger__py_logger.handlers[-1]
    assert isinstance(handler, Async_TimedSizedRotatingFileHandler)

    # Force rotation
    handler.rotation_callback(handler)
    await asyncio.sleep(0)
    await lg.flush()

    rotated = list(tmp_path.glob("rot.log.*"))
    assert len(rotated) >= 1


# ------------------------------------------------------------
# 6. Profiling branches
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_profiling_paths(tmp_path):
    lg = AsyncSmartLogger("profile_test")
    lg.enable_profiling(True)
    lg.add_file(str(tmp_path), "prof.log")

    await lg.a_info("hello")
    await lg.flush()

    text = lg.get_profiling_details()
    assert "Avg total per log" in text


@pytest.mark.asyncio
async def test_profiling_no_data():
    lg = AsyncSmartLogger("profile_empty")
    lg.enable_profiling(True)

    text = lg.get_profiling_details()
    assert text == "No profiling data collected."


# ------------------------------------------------------------
# 7. QueueFull backpressure path
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_queue_full_backpressure(monkeypatch):
    lg = AsyncSmartLogger("queuefull")

    # Force put_nowait to raise QueueFull
    def boom(*args, **kwargs):
        raise asyncio.QueueFull

    monkeypatch.setattr(lg._AsyncSmartLogger__queue, "put_nowait", boom)

    # Should not raise
    await lg.a_info("hello")


# ------------------------------------------------------------
# 8. Audit forwarding edge case
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_logger_does_not_audit_itself(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    audit_logger = AsyncSmartLogger._AsyncSmartLogger__audit_logger

    # Log from audit logger itself
    await audit_logger.a_info("self-test")
    await audit_logger.flush()

    text = (tmp_path / "audit.log").read_text()
    # Should contain only one prefix, not recursive
    assert text.count("[_async_audit]:") == 1
