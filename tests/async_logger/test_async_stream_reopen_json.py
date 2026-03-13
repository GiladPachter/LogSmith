# tests/async_logger/test_async_stream_reopen_json.py
import json
import asyncio
import logging
from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation import RotationLogic, When

import pytest


@pytest.mark.asyncio
async def test_async_stream_reopen_json(tmp_path):
    logic = RotationLogic(when=When.SECOND, interval=1, backupCount=1)

    logger = AsyncSmartLogger("reopen_json", logging.INFO)
    logger.add_file(str(tmp_path), "j.log", rotation_logic=logic, output_mode="json")

    handler = next(
        h for h in logger._py_logger.handlers
        if hasattr(h, "baseFilename")
    )

    handler.stream = None  # simulate lost stream

    await logger.a_info("hello", foo=1)

    await asyncio.sleep(0.05)

    text = (tmp_path / "j.log").read_text().strip()
    data = json.loads(text)

    assert data["fields"]["foo"] == 1


