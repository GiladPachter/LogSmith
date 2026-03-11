import pytest
import logging
from LogSmith import AsyncSmartLogger, OutputMode

@pytest.mark.asyncio
async def test_async_json_formatting(tmp_path):
    logger = AsyncSmartLogger("jsonfmt", logging.INFO)
    logger.add_file(str(tmp_path), "j.log", output_mode=OutputMode.JSON)

    await logger.a_info("hello", user="gilad")
    await logger._queue.join()

    text = (tmp_path / "j.log").read_text()
    assert '"message": "hello"' in text
    assert '"user": "gilad"' in text

@pytest.mark.asyncio
async def test_async_ndjson_formatting(tmp_path):
    logger = AsyncSmartLogger("ndjsonfmt", logging.INFO)
    logger.add_file(str(tmp_path), "n.log", output_mode=OutputMode.NDJSON)

    await logger.a_info("hello")
    await logger._queue.join()

    text = (tmp_path / "n.log").read_text()
    assert text.strip().startswith("{")
    assert text.strip().endswith("}")
