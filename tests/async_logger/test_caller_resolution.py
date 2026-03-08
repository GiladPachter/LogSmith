import asyncio
import logging
import pytest
from pathlib import Path

from LogSmith.async_smartlogger import AsyncSmartLogger


# Helper function to generate a log from a different frame
async def helper_emit(logger, msg):
    await logger.a_info(msg)


@pytest.mark.asyncio
async def test_find_caller_reports_correct_location(tmp_path):
    logger = AsyncSmartLogger("test_find_caller", logging.INFO)
    logger.add_file(str(tmp_path), "caller.log")

    # Emit from helper function so the caller is not this test function
    await helper_emit(logger, "caller-test")
    await logger._queue.join()

    text = (tmp_path / "caller.log").read_text()

    # The log should contain the helper function name and its line number
    assert "helper_emit" in text
    assert "caller-test" in text

    # Ensure it did NOT mistakenly report async_smartlogger internals
    assert "async_smartlogger" not in text
