
import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic
from .harness_async import async_task_flooder

def test_async_concurrency(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        logger = AsyncSmartLogger("async.concurrent", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(str(log_dir), "app.log")

        await async_task_flooder(logger, "hello", tasks=10, messages_per_task=500)

        await logger.flush()
        await logger.shutdown()

        assert (log_dir / "app.log").exists()

    asyncio.run(main())
