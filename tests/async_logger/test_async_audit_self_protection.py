import pytest
import logging
from LogSmith import AsyncSmartLogger

@pytest.mark.asyncio
async def test_async_audit_does_not_mirror_itself(tmp_path):
    logger = AsyncSmartLogger("selfaudit", logging.INFO)
    logger.add_file(str(tmp_path), "a.log")

    # enable audit mode pointing to itself
    AsyncSmartLogger._AsyncSmartLogger__audit_enabled = True
    AsyncSmartLogger._AsyncSmartLogger__audit_logger = logger

    await logger.a_info("hello self")
    await logger._queue.join()

    # flush
    for h in logger._py_logger.handlers:
        h.flush()

    text = (tmp_path / "a.log").read_text()

    # Should appear only once (no recursion)
    assert text.count("hello self") == 1

    AsyncSmartLogger._AsyncSmartLogger__audit_enabled = False
    AsyncSmartLogger._AsyncSmartLogger__audit_logger = None
