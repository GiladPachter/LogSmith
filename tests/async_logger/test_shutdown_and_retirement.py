import logging
import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.formatter import OutputMode


@pytest.mark.asyncio
async def test_stopped_logger_rejects_new_logs(tmp_path):
    logger = AsyncSmartLogger("test_stopped_rejects", logging.INFO)
    logger.add_file(str(tmp_path), "stopped.log")

    # Simulate stop
    logger._stopped = True

    with pytest.raises(RuntimeError):
        await logger.a_info("should fail")


@pytest.mark.asyncio
async def test_retired_logger_rejects_new_logs(tmp_path):
    logger = AsyncSmartLogger("test_retired_rejects", logging.INFO)
    logger.add_file(str(tmp_path), "retired.log")

    logger._retired = True

    with pytest.raises(RuntimeError):
        await logger.a_info("should fail")


@pytest.mark.asyncio
async def test_retired_logger_rejects_handler_additions(tmp_path):
    logger = AsyncSmartLogger("test_retired_handlers", logging.INFO)

    logger._retired = True

    with pytest.raises(RuntimeError):
        logger.add_console()

    with pytest.raises(RuntimeError):
        logger.add_file(str(tmp_path), "x.log")


@pytest.mark.asyncio
async def test_worker_drains_queue_before_exit(tmp_path):
    logger = AsyncSmartLogger("test_drain_before_exit", logging.INFO)
    logger.add_file(str(tmp_path), "drain.log")

    # Enqueue several messages
    for i in range(20):
        await logger.a_info(f"msg {i}")

    # Let worker process
    await logger._queue.join()

    text = (tmp_path / "drain.log").read_text()
    for i in range(20):
        assert f"msg {i}" in text


@pytest.mark.asyncio
async def test_retired_logger_rejects_new_logs(tmp_path):
    logger = AsyncSmartLogger("retire_test", logging.INFO)
    logger.add_file(str(tmp_path), "r.log", output_mode=OutputMode.PLAIN)

    # retire
    logger._retired = True

    with pytest.raises(RuntimeError):
        await logger.a_info("should-fail")

    # but existing queue processing still works (no deadlock)
    await logger._queue.join()
