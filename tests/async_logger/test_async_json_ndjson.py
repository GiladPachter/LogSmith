import pytest
import logging
from LogSmith import AsyncSmartLogger, OutputMode

@pytest.mark.asyncio
async def test_async_json_output(tmp_path):
    logger = AsyncSmartLogger("json_async", logging.INFO)
    logger.add_file(str(tmp_path), "j.log", output_mode=OutputMode.JSON)

    await logger.a_info("hello", user="gilad")
    await logger._queue.join()

    text = (tmp_path / "j.log").read_text()
    assert '"message": "hello"' in text
    assert '"user": "gilad"' in text

@pytest.mark.asyncio
async def test_async_ndjson_output(tmp_path):
    logger = AsyncSmartLogger("ndjson_async", logging.INFO)
    logger.add_file(str(tmp_path), "n.log", output_mode=OutputMode.NDJSON)

    await logger.a_info("hello")
    await logger._queue.join()

    text = (tmp_path / "n.log").read_text()
    assert text.strip().startswith("{") and text.strip().endswith("}")
