# tests/async/test_async_smartlogger_raw.py
import pytest
from pathlib import Path

from LogSmith.async_smartlogger import AsyncSmartLogger

@pytest.mark.asyncio
async def test_raw_to_file(tmp_path):
    lg = AsyncSmartLogger("raw1")
    lg.add_file(str(tmp_path), "raw.log")

    await lg.a_raw("HELLO", end="")
    await lg.flush()

    text = Path(tmp_path / "raw.log").read_text()
    assert "HELLO" in text

@pytest.mark.asyncio
async def test_raw_color_stripping(tmp_path):
    lg = AsyncSmartLogger("raw2")
    lg.add_file(str(tmp_path), "raw2.log", preserve_colors_in_log_files=False)

    await lg.a_raw("\x1b[31mRED\x1b[0m", end="")
    await lg.flush()

    text = Path(tmp_path / "raw2.log").read_text()
    assert "RED" in text
    assert "\x1b" not in text

@pytest.mark.asyncio
async def test_raw_color_preserved(tmp_path):
    lg = AsyncSmartLogger("raw3")
    lg.add_file(str(tmp_path), "raw3.log", preserve_colors_in_log_files=True)

    await lg.a_raw("\x1b[31mRED\x1b[0m", end="")
    await lg.flush()

    text = Path(tmp_path / "raw3.log").read_text()
    assert "\x1b[31m" in text
