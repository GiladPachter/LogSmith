import asyncio
import json
import logging
import pytest
from pathlib import Path

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler
from LogSmith.rotation import RotationLogic, When


@pytest.mark.asyncio
async def test_json_formatting_offloaded(tmp_path):
    """
    JSON formatting is done via asyncio.to_thread(),
    so the handler writes preformatted JSON lines.
    """
    logger = AsyncSmartLogger("test_json_formatting", logging.INFO)

    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="json.log",
        output_mode="json",
    )

    await logger.a_info("hello", user="gilad")
    await logger._queue.join()

    text = (tmp_path / "json.log").read_text().strip()
    data = json.loads(text)

    assert data["message"] == "hello"
    assert data["fields"]["user"] == "gilad"


@pytest.mark.asyncio
async def test_ndjson_formatting(tmp_path):
    logger = AsyncSmartLogger("test_ndjson_formatting", logging.INFO)

    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="ndjson.log",
        output_mode="ndjson",
    )

    await logger.a_info("line1")
    await logger.a_info("line2")
    await logger._queue.join()

    lines = (tmp_path / "ndjson.log").read_text().splitlines()
    assert len(lines) == 2

    obj1 = json.loads(lines[0])
    obj2 = json.loads(lines[1])

    assert obj1["message"] == "line1"
    assert obj2["message"] == "line2"


@pytest.mark.asyncio
async def test_plain_formatting(tmp_path):
    logger = AsyncSmartLogger("test_plain_formatting", logging.INFO)

    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="plain.log",
        output_mode="plain",
    )

    await logger.a_info("plain message")
    await logger._queue.join()

    text = (tmp_path / "plain.log").read_text()
    assert "plain message" in text


@pytest.mark.asyncio
async def test_color_formatting_console(capsys):
    """
    Color formatting should inject ANSI sequences.
    """
    logger = AsyncSmartLogger("test_color_formatting", logging.INFO)
    logger.add_console(output_mode="color")

    await logger.a_info("colored")
    await logger._queue.join()

    captured = capsys.readouterr().out
    assert "colored" in captured
    assert "\x1b[" in captured  # ANSI escape sequence


@pytest.mark.asyncio
async def test_rotating_handler_locking(tmp_path):
    """
    Rotating handlers use handler.write_lock to serialize writes.
    We test that concurrent writes do not corrupt the file.
    """
    logger = AsyncSmartLogger("test_rotating_locking", logging.INFO)

    rotation_logic = RotationLogic(
        maxBytes=10_000,  # large enough to avoid rotation
        backupCount=1,
    )

    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="rotating.log",
        rotation_logic=rotation_logic,
    )

    # Write concurrently from multiple tasks
    async def writer(i):
        await logger.a_info(f"msg {i}")

    tasks = [asyncio.create_task(writer(i)) for i in range(200)]
    await asyncio.gather(*tasks)

    await logger._queue.join()

    text = (tmp_path / "rotating.log").read_text()

    # Ensure all messages appear and no corruption
    for i in range(200):
        assert f"msg {i}" in text
