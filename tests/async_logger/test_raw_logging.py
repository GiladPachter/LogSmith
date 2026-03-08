import asyncio
import logging
import pytest
from pathlib import Path

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.colors import CPrint


@pytest.mark.asyncio
async def test_console_raw_bleaching(capsys):
    """
    Console RAW output should bleach non-colored text by wrapping it
    in the default console color, while preserving ANSI sequences.
    """
    logger = AsyncSmartLogger("test_console_raw_bleach", logging.INFO)
    logger.add_console()

    msg = "plain " + "\x1b[31mred\x1b[0m" + " plain2"
    await logger.a_raw(msg)
    await logger._queue.join()

    out = capsys.readouterr().out

    # Colored segment preserved
    assert "\x1b[31mred\x1b[0m" in out

    # Plain segments recolored with default console color
    assert CPrint.FG.CONSOLE_DEFAULT in out


@pytest.mark.asyncio
async def test_file_raw_sanitization(tmp_path):
    """
    File handlers should strip ANSI sequences unless
    do_not_sanitize_colors_from_string=True.
    """
    logger = AsyncSmartLogger("test_file_raw_sanitize", logging.INFO)
    logger.add_file(str(tmp_path), "raw.log")

    msg = "hello \x1b[32mgreen\x1b[0m world"
    await logger.a_raw(msg)
    await logger._queue.join()

    text = (tmp_path / "raw.log").read_text()

    # ANSI should be stripped
    assert "\x1b[" not in text
    assert "green" in text


@pytest.mark.asyncio
async def test_file_raw_passthrough(tmp_path):
    """
    PassthroughFormatter should preserve ANSI sequences.
    """
    logger = AsyncSmartLogger("test_file_raw_passthrough", logging.INFO)

    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="passthrough.log",
        do_not_sanitize_colors_from_string=True,
    )

    msg = "hello \x1b[35mpurple\x1b[0m world"
    await logger.a_raw(msg)
    await logger._queue.join()

    text = (tmp_path / "passthrough.log").read_text()

    # ANSI preserved
    assert "\x1b[35m" in text
    assert "purple" in text


@pytest.mark.asyncio
async def test_raw_end_parameter(tmp_path):
    """
    RAW logging should respect the 'end' parameter.
    """
    logger = AsyncSmartLogger("test_raw_end", logging.INFO)
    logger.add_file(str(tmp_path), "end.log")

    await logger.a_raw("hello", end="")
    await logger._queue.join()

    text = (tmp_path / "end.log").read_text()
    assert text.endswith("hello")  # no newline


@pytest.mark.asyncio
async def test_raw_stream_reopening(tmp_path):
    """
    If handler.stream is None, RAW logging should reopen it.
    """
    logger = AsyncSmartLogger("test_raw_reopen", logging.INFO)
    logger.add_file(str(tmp_path), "reopen.log")

    handler = logger._py_logger.handlers[0]

    # Simulate closed stream
    handler.stream.close()
    handler.stream = None

    await logger.a_raw("reopened")
    await logger._queue.join()

    text = (tmp_path / "reopen.log").read_text()
    assert "reopened" in text
