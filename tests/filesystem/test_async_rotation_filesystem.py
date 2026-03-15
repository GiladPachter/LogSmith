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


@pytest.mark.asyncio
async def test_async_rotation_creates_rotated_file(clean_async_logger, tmp_path):
    logger = clean_async_logger

    logger.add_file(
        str(tmp_path),
        "x.log",
        rotation_logic=RotationLogic(maxBytes=5, backupCount=3)
    )

    for _ in range(10):
        await logger.a_info("abcdef")

    await logger._queue.join()

    files = sorted(p.name for p in tmp_path.iterdir())
    assert "x.log" in files
    assert "x.log.1" in files
