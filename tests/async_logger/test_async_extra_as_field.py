# tests/async_logger/test_async_extra_as_field.py
import json
import asyncio
import logging
from LogSmith.async_smartlogger import AsyncSmartLogger

import pytest


@pytest.mark.asyncio
async def test_extra_is_structured_field(tmp_path):
    logger = AsyncSmartLogger("extra_field", logging.INFO)
    logger.add_file(str(tmp_path), "x.json", output_mode="json")

    await logger.a_info("hello", extra={"foo": "bar"})
    await asyncio.sleep(0.05)

    text = (tmp_path / "x.json").read_text().strip()
    lines = text.splitlines()

    # find the line containing our message
    target = next(line for line in lines if "hello" in line)

    data = json.loads(target)

    assert data["fields"]["extra"] == {"foo": "bar"}
