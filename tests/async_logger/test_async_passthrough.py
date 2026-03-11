import pytest
import logging
from LogSmith import AsyncSmartLogger, CPrint

@pytest.mark.asyncio
async def test_async_passthrough_formatter(tmp_path):
    logger = AsyncSmartLogger("apass", logging.INFO)
    logger.add_file(
        str(tmp_path),
        "p.log",
        do_not_sanitize_colors_from_string=True,
    )

    colored = CPrint.colorize("HELLO", fg=CPrint.FG.GREEN)
    await logger.a_raw(colored)
    await logger._queue.join()

    text = (tmp_path / "p.log").read_text()
    assert "\x1b" in text  # ANSI preserved
