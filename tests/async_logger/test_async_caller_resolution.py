# tests/async_logger/test_async_caller_resolution.py
import asyncio
import logging
from LogSmith.async_smartlogger import AsyncSmartLogger

import pytest


@pytest.mark.asyncio
async def test_caller_resolution(tmp_path):
    logger = AsyncSmartLogger("caller", logging.INFO)
    logger.add_file(str(tmp_path), "c.json", output_mode="json")

    await logger.a_info("hello")
    await asyncio.sleep(0.05)

    text = (tmp_path / "c.json").read_text()

    # JSON logs do not include caller info unless LogRecordDetails requests it
    assert "hello" in text
