# tests/async_logger/test_async_structured_fields.py
import json
import asyncio
import logging
from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation import RotationLogic, When

import pytest


@pytest.mark.asyncio
async def test_structured_fields_json(tmp_path):
    logger = AsyncSmartLogger("sf_json", logging.INFO)
    logger.add_file(str(tmp_path), "f.json", output_mode="json")

    await logger.a_info("hello", foo=123, bar="xyz")

    await asyncio.sleep(0.05)

    text = (tmp_path / "f.json").read_text().strip()
    data = json.loads(text)

    assert data["message"] == "hello"
    assert data["fields"]["foo"] == 123
    assert data["fields"]["bar"] == "xyz"
