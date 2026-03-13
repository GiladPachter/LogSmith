import pytest
import logging
import os
from LogSmith import AsyncSmartLogger, RotationLogic, When

@pytest.mark.asyncio
async def test_async_handler_reopen(tmp_path):
    logic = RotationLogic(maxBytes=1, backupCount=1)

    logger = AsyncSmartLogger("areopen", logging.INFO)
    logger.add_file(str(tmp_path), "x.log", rotation_logic=logic)

    handler = next(
        h for h in logger._py_logger.handlers
        if hasattr(h, "baseFilename")
    )

    assert hasattr(handler, "_open")  # ensure it's async rotating handler

    # simulate real OS-level stream failure
    os.close(handler.stream.fileno())

    await logger.a_info("hello")
    await logger._queue.join()

    # handler should have reopened stream
    assert handler.stream and not handler.stream.closed
