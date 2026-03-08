import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic


def test_async_no_lock_file(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        rotation = RotationLogic(maxBytes=50, backupCount=2)
        logger = AsyncSmartLogger("async.nolock", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(
            log_dir=str(log_dir),
            logfile_name="app.log",
            rotation_logic=rotation,
        )

        for _ in range(20):
            await logger.a_info("X" * 20)

        await logger.flush()

        lock_files = [p for p in log_dir.iterdir() if p.name.endswith(".lock")]
        assert len(lock_files) == 0

    asyncio.run(main())
