import asyncio
import logging
import os
from pathlib import Path

import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation import RotationLogic, When
from LogSmith.formatter import LogRecordDetails, OutputMode, StructuredJSONFormatter





@pytest.mark.asyncio
async def test_time_rotation_second_boundary(tmp_path):
    logic = RotationLogic(when=When.SECOND, interval=1, backupCount=2)

    logger = AsyncSmartLogger("time_rot_sec", logging.INFO)
    logger.add_file(str(tmp_path), "t.log", rotation_logic=logic, output_mode=OutputMode.PLAIN)

    # log across a second boundary
    await logger.a_info("before")
    await asyncio.sleep(1.1)
    await logger.a_info("after")
    await logger._queue.join()

    files = sorted(p.name for p in tmp_path.glob("t.log*"))
    # base + at least one rotated file
    assert "t.log" in files
    assert any(name.startswith("t.log.") for name in files)
