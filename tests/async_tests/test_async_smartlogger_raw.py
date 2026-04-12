import logging

import pytest
from pathlib import Path
from LogSmith.async_smartlogger import AsyncSmartLogger


@pytest.mark.asyncio
async def test_raw_console_bleaches_color(capsys):
    logger = AsyncSmartLogger("raw_bleach")
    logger.add_console()

    # Contains ANSI color
    msg = "\x1b[31mRED\x1b[0m plain"

    await logger.a_raw(logging.INFO, msg)
    await logger.flush()

    out = capsys.readouterr().out

    # Console RAW should bleach non-colored text but preserve ANSI sequences
    assert "RED" in out
    assert "\x1b[31m" in out  # color preserved
    assert "plain" in out


@pytest.mark.asyncio
async def test_raw_file_strips_ansi(tmp_path):
    logger = AsyncSmartLogger("raw_file_strip")

    log_dir = str(tmp_path)
    logger.add_file(log_dir=log_dir, preserve_colors_in_log_files=False)

    msg = "\x1b[32mGREEN\x1b[0m plain"

    await logger.a_raw(logging.INFO, msg)
    await logger.flush()
    await logger.shutdown()

    file_path = Path(log_dir) / "raw_file_strip.log"
    text = file_path.read_text()

    # ANSI should be stripped for file handlers unless preserve_colors=True
    assert "GREEN" in text
    assert "\x1b[32m" not in text


@pytest.mark.asyncio
async def test_raw_file_preserves_ansi(tmp_path):
    logger = AsyncSmartLogger("raw_file_preserve")

    log_dir = str(tmp_path)
    logger.add_file(log_dir=log_dir, preserve_colors_in_log_files=True)

    msg = "\x1b[35mMAGENTA\x1b[0m plain"

    await logger.a_raw(logging.INFO, msg)
    await logger.flush()
    await logger.shutdown()

    file_path = Path(log_dir) / "raw_file_preserve.log"
    text = file_path.read_text()

    # ANSI should be preserved
    assert "\x1b[35m" in text
    assert "MAGENTA" in text


@pytest.mark.asyncio
async def test_raw_reopens_file_if_stream_none(tmp_path, monkeypatch):
    logger = AsyncSmartLogger("raw_reopen")

    log_dir = str(tmp_path)
    logger.add_file(log_dir=log_dir)

    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    # Simulate closed stream
    handler.stream.close()
    handler.stream = None

    await logger.a_raw(logging.INFO, "hello")
    await logger.flush()
    await logger.shutdown()

    file_path = Path(log_dir) / "raw_reopen.log"
    assert file_path.read_text().strip() == "hello"


@pytest.mark.asyncio
async def test_raw_write_error_is_swallowed(tmp_path, monkeypatch):
    logger = AsyncSmartLogger("raw_error")

    log_dir = str(tmp_path)
    logger.add_file(log_dir=log_dir)

    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    # Force write() to fail
    def bad_write(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(handler.stream, "write", bad_write)

    # Should not crash
    await logger.a_raw(logging.INFO, "hello")
    await logger.flush()
    await logger.shutdown()
