import asyncio
import logging
import pytest

from LogSmith import RotationLogic, When, OutputMode
from LogSmith.async_smartlogger import AsyncSmartLogger, AsyncOp, _QueueItem


@pytest.mark.asyncio
async def test_worker_starts_automatically():
    logger = AsyncSmartLogger("test_worker_start", logging.INFO)

    # Worker tasks should exist and be running
    assert hasattr(logger, "_worker_tasks")
    assert len(logger._worker_tasks) >= 1
    for task in logger._worker_tasks:
        assert not task.done()


@pytest.mark.asyncio
async def test_worker_drains_queue(tmp_path):
    logger = AsyncSmartLogger("test_worker_drain", logging.INFO)
    logger.add_console()

    await logger.a_info("hello")
    await logger.a_info("world")

    # Wait for queue to drain
    await asyncio.sleep(0)  # yield to worker
    await logger._queue.join()

    assert AsyncSmartLogger.messages_processed() >= 2


@pytest.mark.asyncio
async def test_worker_stops_on_sentinel():
    logger = AsyncSmartLogger("test_worker_sentinel", logging.INFO)

    # Enqueue sentinel
    await logger._queue.put(_QueueItem(op=AsyncOp.SENTINEL, payload={}))

    # Wait for worker to exit
    for task in logger._worker_tasks:
        await task

    assert all(task.done() for task in logger._worker_tasks)


@pytest.mark.asyncio
async def test_worker_fifo_order(tmp_path):
    logger = AsyncSmartLogger("test_worker_fifo", logging.INFO)

    log_path = tmp_path / "fifo.log"
    logger.add_file(str(tmp_path), "fifo.log")

    await logger.a_info("first")
    await logger.a_info("second")
    await logger.a_info("third")

    await logger._queue.join()

    text = log_path.read_text()
    assert "first" in text
    assert "second" in text
    assert "third" in text

    # Ensure order
    assert text.index("first") < text.index("second") < text.index("third")


@pytest.mark.asyncio
async def test_async_worker_survives_formatter_exception(tmp_path):
    logger = AsyncSmartLogger("x")

    class BadFormatter(logging.Formatter):
        def format(self, record):
            raise RuntimeError("format fail")

    logger.add_file(
        str(tmp_path),
        "x.log",
        rotation_logic=RotationLogic(when=When.SECOND, interval=1),
        output_mode=OutputMode.PLAIN,
    )

    # Patch the actual handler's formatter
    handler = logger._py_logger.handlers[0]
    handler.setFormatter(BadFormatter())

    before = logger.messages_processed()

    await logger.a_info("hello")
    await logger._queue.join()

    after = logger.messages_processed()

    assert after == before



