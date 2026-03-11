import pytest
import logging
from LogSmith import AsyncSmartLogger

@pytest.mark.asyncio
async def test_async_logger_retired_raises(tmp_path):
    logger = AsyncSmartLogger("retired", logging.INFO)
    logger.add_file(str(tmp_path), "x.log")

    logger._retired = True
    with pytest.raises(RuntimeError):
        await logger.a_info("should fail")

@pytest.mark.asyncio
async def test_async_logger_stopped_raises(tmp_path):
    logger = AsyncSmartLogger("stopped", logging.INFO)
    logger.add_file(str(tmp_path), "x.log")

    logger._stopped = True
    with pytest.raises(RuntimeError):
        await logger.a_raw("raw fail")
