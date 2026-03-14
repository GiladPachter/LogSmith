import asyncio
import time
from pathlib import Path

import pytest

from LogSmith import AsyncSmartLogger
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.rotation_base import RotationLogic, When


async def test_async_rotation(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    rotation = RotationLogic(maxBytes=100, backupCount=2)
    logger = AsyncSmartLogger("fs.async", level=AsyncSmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=rotation)

    for i in range(50):
        await logger.a_info("X" * 30)

    await logger._queue.join()

    rotated = [p for p in log_dir.iterdir() if p.name.startswith("app.log.") and not p.name.endswith(".lock")]
    assert len(rotated) <= 2


