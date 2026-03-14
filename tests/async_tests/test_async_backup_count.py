import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic


def test_async_backup_count(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        rotation = RotationLogic(maxBytes=50, backupCount=2)
        logger = AsyncSmartLogger("async.backup", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(
            log_dir=str(log_dir),
            logfile_name="app.log",
            rotation_logic=rotation,
        )

        for _ in range(50):
            await logger.a_info("X" * 20)

        # flush is fine to call from async context even if it's sync
        await logger.flush()

        rotated = [
            p for p in log_dir.iterdir()
            if p.name.startswith("app.log.") and not p.name.endswith(".lock")
        ]
        assert len(rotated) <= 2

    asyncio.run(main())
