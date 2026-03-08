
import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from .harness_shutdown import shutdown_race_tester

def test_shutdown_race(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        logger = AsyncSmartLogger("shutdown.race", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(str(log_dir), "app.log")

        await shutdown_race_tester(logger)

        # shutdown_race_tester already calls shutdown()

        assert (log_dir / "app.log").exists()

    asyncio.run(main())
