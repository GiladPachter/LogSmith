import pytest
import logging
from LogSmith import AsyncSmartLogger, CPrint

@pytest.mark.asyncio
async def test_async_passthrough_formatter(tmp_path):
    logger = AsyncSmartLogger("apass", logging.INFO)
    logger.add_file(
        str(tmp_path),
        "p.log",
        preserve_colors_in_log_files=True,
    )

    colored = CPrint.colorize("HELLO", fg=CPrint.FG.GREEN)
    await logger.a_raw(logging.INFO, colored)
    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    text = (tmp_path / "p.log").read_text()
    assert "\x1b" in text  # ANSI preserved
