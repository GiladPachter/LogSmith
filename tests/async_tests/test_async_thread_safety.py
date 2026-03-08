import asyncio
import threading
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic


def test_async_thread_safety(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        rotation = RotationLogic(maxBytes=200, backupCount=3)
        logger = AsyncSmartLogger("async.threads", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(
            log_dir=str(log_dir),
            logfile_name="app.log",
            rotation_logic=rotation,
        )

        loop = asyncio.get_running_loop()

        def worker():
            for _ in range(200):
                # Submit async logging from a thread
                asyncio.run_coroutine_threadsafe(
                    logger.a_info("thread message"),
                    loop,
                )

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()

        await logger.flush()
        await logger.shutdown()

        assert (log_dir / "app.log").exists()

    asyncio.run(main())
