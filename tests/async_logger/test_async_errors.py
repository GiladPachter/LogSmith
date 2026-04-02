import pytest
import logging
from LogSmith import AsyncSmartLogger

@pytest.mark.asyncio
async def test_async_logger_retired_raises(tmp_path):
    logger = AsyncSmartLogger("retired", logging.INFO)
    logger.add_file(str(tmp_path), "x.log")

    # logger.__retired = True
    logger._AsyncSmartLogger__retired = True    # accessing private member. do not use outside of test suite
    with pytest.raises(RuntimeError):
        await logger.a_info("should fail")

    logger.destroy()

@pytest.mark.asyncio
async def test_async_logger_stopped_raises(tmp_path):
    logger = AsyncSmartLogger("stopped", logging.INFO)
    logger.add_file(str(tmp_path), "x.log")

    # logger._stopped = True
    logger._AsyncSmartLogger__stopped = True
    with pytest.raises(RuntimeError):
        await logger.a_raw("raw fail")

    logger.destroy()
