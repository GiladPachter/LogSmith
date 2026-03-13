
import asyncio
import logging
from pathlib import Path

import pytest

from LogSmith import AsyncSmartLogger, OutputMode
from .harness_queue import queue_pressure_tester

def test_queue_pressure(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        logger = AsyncSmartLogger("queue.pressure", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(str(log_dir), "app.log")

        await queue_pressure_tester(logger, messages=15000)

        await logger.flush()
        await logger.shutdown()

        assert (log_dir / "app.log").exists()

    asyncio.run(main())


@pytest.mark.asyncio
async def test_backpressure_large_queue(tmp_path):
    logger = AsyncSmartLogger("backpressure", logging.INFO)
    logger.add_file(str(tmp_path), "bp.log", output_mode=OutputMode.PLAIN)

    async def spam(n):
        for i in range(n):
            await logger.a_info(f"bp-{i}")

    # push a lot of messages
    await spam(20000)
    await logger._queue.join()

    text = (tmp_path / "bp.log").read_text(encoding="utf-8")
    # spot-check some messages
    assert "bp-0" in text
    assert "bp-19999" in text
