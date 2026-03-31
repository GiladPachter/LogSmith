# tests/async/test_async_smartlogger_rotation.py
import asyncio
import logging
import os
import threading
import pytest
from pathlib import Path

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler


# ------------------------------------------------------------
# 1. Normal rotation pipeline (your existing test)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_async_rotation_pipeline(tmp_path):
    log_dir = tmp_path
    file = "rot.log"

    logic = RotationLogic(maxBytes=1, append_filename_pid=True)

    lg = AsyncSmartLogger("rot")
    lg.add_file(str(log_dir), file, rotation_logic=logic)

    for _ in range(3):
        await lg.a_info("X")

    await lg.flush()
    await asyncio.sleep(0.05)

    rotated = [f for f in os.listdir(log_dir) if f.startswith("rot.log.")]
    assert rotated, "Rotation did not occur"


# ------------------------------------------------------------
# 2. Direct worker-side rotation call (your existing test)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_process_rotate_direct_call(tmp_path):
    log_file = tmp_path / "direct.log"
    handler = Async_TimedSizedRotatingFileHandler(str(log_file), max_bytes=1)

    flag = {"rotated": False}

    def fake_rotate():
        flag["rotated"] = True

    handler.perform_rotation = fake_rotate

    lg = AsyncSmartLogger("rot2")
    await lg._AsyncSmartLogger__process_rotate({"handler": handler})

    assert flag["rotated"] is True


# ------------------------------------------------------------
# 3. Rotation enqueue from SAME thread (direct put_nowait path)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_rotation_enqueue_same_thread(tmp_path):
    lg = AsyncSmartLogger("rot3")
    lg.add_file(str(tmp_path), "same.log", rotation_logic=RotationLogic(maxBytes=1))

    handler = lg._AsyncSmartLogger__py_logger.handlers[0]

    # Discover callback dynamically
    callback_attr = [k for k in vars(handler) if "callback" in k][0]
    callback = getattr(handler, callback_attr)

    # Trigger rotation
    callback(handler)

    await lg.flush()
    await asyncio.sleep(0.05)

    rotated = [f for f in os.listdir(tmp_path) if f.startswith("same.log.")]
    assert rotated


# ------------------------------------------------------------
# 4. Rotation enqueue from DIFFERENT thread (call_soon_threadsafe path)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_rotation_enqueue_cross_thread(tmp_path):
    lg = AsyncSmartLogger("rot4")
    lg.add_file(str(tmp_path), "cross.log", rotation_logic=RotationLogic(maxBytes=1))

    handler = lg._AsyncSmartLogger__py_logger.handlers[0]

    # Write enough to trigger rollover
    def call_from_thread():
        # This forces the handler to check rollover and call the callback internally
        handler.emit(handler.format(logging.LogRecord(
            name="x",
            level=20,
            pathname=__file__,
            lineno=1,
            msg="X",
            args=(),
            exc_info=None
        )))

    t = threading.Thread(target=call_from_thread)
    t.start()
    t.join()

    await lg.flush()
    await asyncio.sleep(0.05)

    rotated = [f for f in os.listdir(tmp_path) if f.startswith("cross.log.")]
    assert rotated


# ------------------------------------------------------------
# 5. Rotation with handler.stream = None (reopen stream branch)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_rotation_reopens_stream(tmp_path):
    lg = AsyncSmartLogger("rot5")
    lg.add_file(str(tmp_path), "reopen.log", rotation_logic=RotationLogic(maxBytes=1))

    handler = lg._AsyncSmartLogger__py_logger.handlers[0]

    # Force stream to None, to hit reopen branch
    handler.stream = None

    # Trigger rotation
    handler.rotation_callback(handler)

    await lg.flush()
    await asyncio.sleep(0.05)

    rotated = [f for f in os.listdir(tmp_path) if f.startswith("reopen.log.")]
    assert rotated


# ------------------------------------------------------------
# 6. Rotation perform_rotation raises (worker must swallow exception)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_rotation_exception_swallowed(tmp_path):
    lg = AsyncSmartLogger("rot6")
    lg.add_file(str(tmp_path), "err.log", rotation_logic=RotationLogic(maxBytes=1))

    handler = lg._AsyncSmartLogger__py_logger.handlers[0]

    def bad_rotate():
        raise RuntimeError("boom")

    handler.perform_rotation = bad_rotate

    handler.rotation_callback(handler)

    # Worker must not crash
    await lg.a_info("still works")
    await lg.flush()

    text = Path(tmp_path / "err.log").read_text()
    assert "still works" in text
