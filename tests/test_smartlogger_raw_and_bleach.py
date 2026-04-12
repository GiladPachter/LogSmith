import logging

import pytest

from LogSmith import SmartLogger, CPrint, AsyncSmartLogger


def test_raw_output_and_bleaching(tmp_path):
    logger = SmartLogger("bleach", logging.INFO)
    logger.add_file(str(tmp_path), "b.log")

    colored = CPrint.colorize("HELLO", fg=CPrint.FG.RED)
    logger.raw(logging.INFO, colored)

    text = (tmp_path / "b.log").read_text()
    assert "HELLO" in text
    assert "\x1b" not in text  # stripped

def test_passthrough_formatter(tmp_path):
    logger = SmartLogger("pass", logging.INFO)
    logger.add_file(str(tmp_path), "p.log", preserve_colors_in_log_files=True)

    colored = CPrint.colorize("HELLO", fg=CPrint.FG.GREEN)
    logger.raw(logging.INFO, colored)

    text = (tmp_path / "p.log").read_text()
    assert "\x1b" in text  # ANSI preserved

def test_smartlogger_raw(tmp_path):
    log = SmartLogger("x")
    log.add_file(str(tmp_path), "x.log")

    log.raw(logging.INFO, "hello", end="")
    assert (tmp_path / "x.log").read_text() == "hello"

    log.destroy()


@pytest.mark.asyncio
async def test_async_raw(tmp_path):
    logger = AsyncSmartLogger("x")
    logger.add_file(str(tmp_path), "x.log")

    await logger.a_raw("hello", end="")
    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    assert (tmp_path / "x.log").read_text() == "hello"

    await logger.destroy()
