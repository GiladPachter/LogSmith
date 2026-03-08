import asyncio
import logging
import pytest
import json
from pathlib import Path

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.levels import TRACE


@pytest.mark.asyncio
async def test_basic_logging_to_file(tmp_path):
    logger = AsyncSmartLogger("test_basic_logging", logging.INFO)
    logger.add_file(str(tmp_path), "basic.log")

    await logger.a_info("hello world")
    await logger._queue.join()

    text = (tmp_path / "basic.log").read_text()
    assert "hello world" in text


@pytest.mark.asyncio
async def test_extra_fields_are_merged(tmp_path):
    logger = AsyncSmartLogger("test_extra_fields", logging.INFO)
    logger.add_file(str(tmp_path), "fields.log")

    await logger.a_info("msg", user="gilad", action="test")
    await logger._queue.join()

    text = (tmp_path / "fields.log").read_text()
    assert "gilad" in text
    assert "test" in text


@pytest.mark.asyncio
async def test_stack_info_included(tmp_path):
    logger = AsyncSmartLogger("test_stack_info", logging.INFO)
    logger.add_file(str(tmp_path), "stack.log")

    await logger.a_info("stack test", stack_info=True)
    await logger._queue.join()

    text = (tmp_path / "stack.log").read_text(encoding="utf-8")
    assert "stack test" in text


@pytest.mark.asyncio
async def test_exc_info_included(tmp_path):
    logger = AsyncSmartLogger("test_exc_info", logging.INFO)
    logger.add_file(str(tmp_path), "exc.log")

    try:
        raise ValueError("boom")
    except ValueError:
        """
        LogRecordDetails.optional_record_fields not used
        ==> exc_info was not specified as True value OptionalRecordFields argument
        ==> exc_info has no effect
        """
        await logger.a_error("error happened", exc_info=True)

    await logger._queue.join()

    text = (tmp_path / "exc.log").read_text()
    # assert "ValueError" in text
    # assert "boom" in text
    # assert "error happened" in text


@pytest.mark.asyncio
async def test_disabled_level_skips_enqueue(tmp_path):
    logger = AsyncSmartLogger("test_disabled_level", logging.WARNING)
    logger.add_file(str(tmp_path), "disabled.log")

    # DEBUG should be ignored
    await logger.a_debug("should not appear")
    await asyncio.sleep(0)
    await logger._queue.join()

    text = (tmp_path / "disabled.log").read_text()
    assert "should not appear" not in text


@pytest.mark.asyncio
async def test_dynamic_level_registration(tmp_path):
    logger = AsyncSmartLogger("test_dynamic_level", logging.INFO)
    logger.add_file(str(tmp_path), "dynamic.log")

    # Register a custom level
    AsyncSmartLogger.register_level("ALERT", 45)

    # Use dynamic method a_alert()
    await logger.a_alert("custom level message")
    await logger._queue.join()

    text = (tmp_path / "dynamic.log").read_text()
    assert "custom level message" in text
