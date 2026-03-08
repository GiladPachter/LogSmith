import asyncio
import time
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic


def test_async_emit_non_blocking(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        rotation = RotationLogic(maxBytes=20, backupCount=2)
        logger = AsyncSmartLogger("async.nonblock", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(
            log_dir=str(log_dir),
            logfile_name="app.log",
            rotation_logic=rotation,
        )

        start = time.time()
        for _ in range(200):
            logger.a_info("X" * 50)
        end = time.time()

        await logger.flush()

        assert (end - start) < 0.2

    asyncio.run(main())
