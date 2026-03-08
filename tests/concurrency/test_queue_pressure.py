
import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
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
