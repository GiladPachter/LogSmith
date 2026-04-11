# tests/async/test_async_smartlogger_lifecycle.py
import pytest
from pathlib import Path

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.levels import LevelStyle
from LogSmith.colors import CPrint

@pytest.mark.asyncio
async def test_flush_and_shutdown(tmp_path):
    lg = AsyncSmartLogger("life1")
    lg.add_file(str(tmp_path), "life.log")

    await lg.a_info("A")
    await lg.flush()

    await lg.shutdown()
    with pytest.raises(RuntimeError):
        await lg.a_info("B")

@pytest.mark.asyncio
async def test_retire_and_destroy(tmp_path):
    lg = AsyncSmartLogger("life2")
    lg.add_file(str(tmp_path), "life2.log")

    lg.retire()
    with pytest.raises(RuntimeError):
        await lg.a_info("X")

    await lg.destroy()
    assert lg._AsyncSmartLogger__handlers == []

def test_get_record_exc_and_stack():
    try:
        raise ValueError("boom")
    except Exception:
        rec = AsyncSmartLogger.get_record(exc_info=True, stack_info=True)

    assert rec.exc_info is not None
    assert rec.stack_info is not None

@pytest.mark.asyncio
async def test_dynamic_level_and_theme(tmp_path):
    lg = AsyncSmartLogger("life3")
    lg.add_file(str(tmp_path), "life3.log")

    AsyncSmartLogger.register_level("NOTICE", 25, LevelStyle(fg=CPrint.FG.GREEN))
    await lg.a_notice("hello")
    await lg.flush()

    text = Path(tmp_path / "life3.log").read_text()
    assert "hello" in text
