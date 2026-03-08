
import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic
from .harness_async import async_task_flooder
from .harness_rotation import inspect_rotation

def test_rotation_concurrency(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        rotation = RotationLogic(maxBytes=2000, backupCount=5)

        logger = AsyncSmartLogger("rotate.concurrent", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(str(log_dir), "app.log", rotation_logic=rotation)

        await async_task_flooder(logger, "rotation test", tasks=10, messages_per_task=1000)

        await logger.flush()
        await logger.shutdown()

        base_exists, rotated, numbers = inspect_rotation(log_dir, "app.log")

        assert base_exists
        assert len(rotated) >= 1
        assert numbers == sorted(numbers)

    asyncio.run(main())
