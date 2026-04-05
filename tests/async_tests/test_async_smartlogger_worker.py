import pytest
import asyncio
import logging
from LogSmith.async_smartlogger import AsyncSmartLogger


# ------------------------------------------------------------
# 1. Duplicate console handler suppression (371–374)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_duplicate_console_handler():
    logger = AsyncSmartLogger("dup_console")
    logger.add_console()
    logger.add_console()  # should be ignored

    handlers = logger._AsyncSmartLogger__py_logger.handlers
    assert len(handlers) == 1

    await logger.shutdown()

    logger.destroy()


# ------------------------------------------------------------
# 2. Duplicate file handler detection (468–485)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_duplicate_file_handler(tmp_path):
    log_dir = str(tmp_path)
    logfile = "dup.log"

    logger1 = AsyncSmartLogger("L1")
    logger2 = AsyncSmartLogger("L2")

    logger1.add_file(log_dir=log_dir, logfile_name=logfile)

    with pytest.raises(ValueError):
        logger2.add_file(log_dir=log_dir, logfile_name=logfile)

    await logger1.shutdown()
    await logger2.shutdown()

    logger1.destroy()
    logger2.destroy()


# ------------------------------------------------------------
# 3. Worker exception swallowing (507)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_worker_swallows_exceptions(monkeypatch):
    logger = AsyncSmartLogger("worker_exc")

    async def bad_process_log(*args, **kwargs):
        raise RuntimeError("boom")

    # Patch the method actually called inside worker
    monkeypatch.setattr(
        logger,
        "_AsyncSmartLogger__process_log",
        bad_process_log
    )

    await logger.a_info("hello")  # enqueues LOG
    await logger.flush()          # worker should swallow exception

    await logger.shutdown()


# ------------------------------------------------------------
# 4. Shutdown sends sentinel (536–539)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_shutdown_sends_sentinel():
    logger = AsyncSmartLogger("sentinel_test")
    await logger.a_info("x")  # ensure worker started

    tasks = list(logger._AsyncSmartLogger__worker_tasks)

    await logger.shutdown()

    for t in tasks:
        assert t.done()

    logger.destroy()


# ------------------------------------------------------------
# 5. Shutdown after retire (565–566)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_shutdown_after_retire():
    logger = AsyncSmartLogger("retire_shutdown")
    logger.retire()

    # Should not hang or crash
    await logger.shutdown()


# ------------------------------------------------------------
# 6. Shutdown twice (592, 594)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_shutdown_twice():
    logger = AsyncSmartLogger("shutdown_twice")

    await logger.shutdown()
    await logger.shutdown()  # second call hits uncovered branch
