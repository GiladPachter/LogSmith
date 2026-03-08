import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic, When


def test_async_time_rotation(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        rotation = RotationLogic(
            when=When.SECOND,
            interval=1,
            backupCount=3,
        )

        logger = AsyncSmartLogger("async.time", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(
            log_dir=str(log_dir),
            logfile_name="app.log",
            rotation_logic=rotation,
        )

        await logger.a_info("start")
        await asyncio.sleep(1.2)
        await logger.a_info("after rollover")

        await logger.flush()
        await logger.shutdown()

        rotated = [
            p for p in log_dir.iterdir()
            if p.name.startswith("app.log.") and not p.name.endswith(".lock")
        ]
        assert len(rotated) >= 1

    asyncio.run(main())
