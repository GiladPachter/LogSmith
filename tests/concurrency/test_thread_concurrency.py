
import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic
from .harness_threads import thread_flooder

def test_thread_concurrency(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        logger = AsyncSmartLogger("thread.concurrent", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(str(log_dir), "app.log")

        loop = asyncio.get_running_loop()

        thread_flooder(logger, loop, "thread msg", threads=5, messages_per_thread=1000)

        await logger.flush()
        await logger.shutdown()

        assert (log_dir / "app.log").exists()

    asyncio.run(main())
