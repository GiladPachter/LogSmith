# tests/async/test_async_smartlogger_rotation.py
import asyncio
import os
import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic

@pytest.mark.asyncio
async def test_async_rotation_pipeline(tmp_path):
    log_dir = tmp_path
    file = "rot.log"

    logic = RotationLogic(maxBytes=1, append_filename_pid=True)

    lg = AsyncSmartLogger("rot")
    lg.add_file(str(log_dir), file, rotation_logic=logic)

    # Trigger rotation
    for _ in range(3):
        await lg.a_info("X")

    await lg.flush()
    await asyncio.sleep(0.05)

    rotated = [f for f in os.listdir(log_dir) if f.startswith("rot.log.")]

    assert rotated, "Rotation did not occur"

@pytest.mark.asyncio
async def test_process_rotate_direct_call(tmp_path):
    # Directly exercise __process_rotate
    from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler

    log_file = tmp_path / "direct.log"
    handler = Async_TimedSizedRotatingFileHandler(str(log_file), max_bytes=1)

    flag = {"rotated": False}

    def fake_rotate():
        flag["rotated"] = True

    handler.perform_rotation = fake_rotate

    lg = AsyncSmartLogger("rot2")

    await lg._AsyncSmartLogger__process_rotate({"handler": handler})

    assert flag["rotated"] is True
