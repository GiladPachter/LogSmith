import pytest
import logging
from LogSmith import AsyncSmartLogger

@pytest.mark.asyncio
async def test_async_profiling_basic(tmp_path):
    logger = AsyncSmartLogger("profiler", logging.INFO)
    logger.add_file(str(tmp_path), "p.log")

    # Initially no profiling
    assert logger.get_profiling_details() == "Profiling not enabled."

    logger.enable_profiling(True)
    await logger.a_info("hello")
    await logger._queue.join()

    details = logger.get_profiling_details()
    assert "Total log events:" in details
    assert "Avg find_caller:" in details
    assert "Avg handler time:" in details

    logger.enable_profiling(False)
    assert logger.get_profiling_details() == "Profiling not enabled."
