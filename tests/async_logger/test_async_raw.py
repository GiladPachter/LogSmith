# tests/async_logger/test_async_raw.py
import asyncio
import logging
from LogSmith.async_smartlogger import AsyncSmartLogger

import pytest


@pytest.mark.asyncio
async def test_raw_logging(tmp_path):
    logger = AsyncSmartLogger("raw", logging.INFO)
    logger.add_file(str(tmp_path), "raw.log")

    await logger.a_raw("HELLO_RAW")

    await asyncio.sleep(0.05)

    text = (tmp_path / "raw.log").read_text()
    assert "HELLO_RAW" in text
