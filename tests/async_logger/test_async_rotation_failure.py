import pytest
import logging
from unittest.mock import patch
from LogSmith import AsyncSmartLogger, RotationLogic, When

@pytest.mark.asyncio
async def test_async_rotation_failure_does_not_crash(tmp_path):
    logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        backupCount=1,
    )

    logger = AsyncSmartLogger("arotfail", logging.INFO)
    logger.add_file(str(tmp_path), "a.log", rotation_logic=logic)

    with patch("os.rename", side_effect=OSError("fail")):
        await logger.a_info("x" * 5000)

    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # this is an abuse. do not use outside of test suite

    assert (tmp_path / "a.log").exists()
