import pytest
import logging
import time
from LogSmith import AsyncSmartLogger, RotationLogic, When

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
