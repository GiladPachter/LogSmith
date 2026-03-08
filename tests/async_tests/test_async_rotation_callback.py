import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic


def test_async_rotation_happens(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        rotation = RotationLogic(maxBytes=30, backupCount=2)
        logger = AsyncSmartLogger("async.rotate", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(
            log_dir=str(log_dir),
            logfile_name="app.log",
            rotation_logic=rotation,
        )

        # Write enough to trigger rotation
        for _ in range(20):
            await logger.a_info("X" * 20)
            await asyncio.sleep(0)  # > 0.01s throttle

        await logger.flush()

        rotated = [
            p for p in log_dir.iterdir()
            if p.name.startswith("app.log.") and not p.name.endswith(".lock")
        ]

        assert len(rotated) >= 1

    asyncio.run(main())
