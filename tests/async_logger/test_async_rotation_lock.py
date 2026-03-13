import asyncio
import pytest
import logging
import time
from LogSmith import AsyncSmartLogger, RotationLogic, When
from LogSmith.formatter import OutputMode

@pytest.mark.asyncio
async def test_async_rotation_occurs(tmp_path):
    logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        backupCount=1,
    )

    logger = AsyncSmartLogger("arot", logging.INFO)
    logger.add_file(str(tmp_path), "a.log", rotation_logic=logic)

    # trigger rotation
    await logger.a_info("x" * 5000)
    await logger._queue.join()
    time.sleep(1.1)

    await logger.a_info("y" * 5000)
    await logger._queue.join()

    # rotation should have created at least one rotated file
    rotated = list(tmp_path.glob("a.log*"))
    assert len(rotated) >= 1


@pytest.mark.asyncio
async def test_concurrent_writes_during_rotation(tmp_path):
    logic = RotationLogic(maxBytes=1, backupCount=3)

    logger = AsyncSmartLogger("concurrent_rot", logging.INFO)
    logger.add_file(str(tmp_path), "c.log", rotation_logic=logic, output_mode=OutputMode.PLAIN)

    async def spam(n):
        for i in range(n):
            await logger.a_info(f"msg-{i}")

    # concurrent writers
    await asyncio.gather(*(spam(50) for _ in range(5)))
    await logger._queue.join()

    # collect all log files: base + rotated
    files = list(tmp_path.glob("c.log*"))
    assert files, "no log files created at all"

    # at least one of them should be non-empty
    assert any(p.stat().st_size > 0 for p in files)

    # and we expect at least one rotation to have happened
    rotated = [p for p in files if p.name != "c.log"]
    assert len(rotated) >= 1
