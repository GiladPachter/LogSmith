import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic, ExpirationRule, ExpirationScale


def test_async_expiration(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        rotation = RotationLogic(
            maxBytes=30,
            backupCount=10,
            expiration_rule=ExpirationRule(ExpirationScale.Seconds, interval=0),
        )

        logger = AsyncSmartLogger("async.expire", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(
            log_dir=str(log_dir),
            logfile_name="app.log",
            rotation_logic=rotation,
        )

        for _ in range(20):
            await logger.a_info("X" * 20)

        await logger.flush()

        rotated = [
            p for p in log_dir.iterdir()
            if p.name.startswith("app.log.") and not p.name.endswith(".lock")
        ]

        assert len(rotated) == 0

    asyncio.run(main())
