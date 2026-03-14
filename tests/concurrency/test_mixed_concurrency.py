
import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic
from .harness_mixed import mixed_flooder

def test_mixed_concurrency(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        logger = AsyncSmartLogger("mixed.concurrent", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(str(log_dir), "app.log")

        loop = asyncio.get_running_loop()

        await mixed_flooder(logger, loop)

        await logger.flush()
        await logger.shutdown()

        assert (log_dir / "app.log").exists()

    asyncio.run(main())
