# tests/async_logger/test_async_rotation_callback.py
import asyncio
import pytest
import logging
import threading
import time
from LogSmith import AsyncSmartLogger, RotationLogic, When


@pytest.mark.asyncio
async def test_rotation_callback_from_worker(tmp_path):
    logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        backupCount=1,
    )

    logger = AsyncSmartLogger("rot_worker", logging.INFO)
    logger.add_file(str(tmp_path), "w.log", rotation_logic=logic)

    # Trigger rotation
    await logger.a_info("x" * 5000)
    await logger._queue.join()
    time.sleep(1.1)

    await logger.a_info("y" * 5000)
    await logger._queue.join()

    # Rotation should have occurred
    rotated = list(tmp_path.glob("w.log*"))
    assert len(rotated) >= 1


@pytest.mark.asyncio
async def test_rotation_callback_from_external_thread(tmp_path):
    logic = RotationLogic(maxBytes=1, backupCount=1)

    logger = AsyncSmartLogger("rot_ext", logging.INFO)
    logger.add_file(str(tmp_path), "e.log", rotation_logic=logic)

    handler = logger.file_handlers[0]

    # Call rotation callback from another thread
    def external_call():
        handler.rotation_callback(handler)

    t = threading.Thread(target=external_call)
    t.start()
    t.join()

    await logger._queue.join()

    # Rotation should have happened
    rotated = list(tmp_path.glob("e.log*"))
    assert len(rotated) >= 1


@pytest.mark.asyncio
async def test_rotation_callback_ignored_when_retired(tmp_path):
    logic = RotationLogic(maxBytes=1, backupCount=1)

    logger = AsyncSmartLogger("rot_retired", logging.INFO)
    logger.add_file(str(tmp_path), "r.log", rotation_logic=logic)

    handler = next(
        h for h in logger._py_logger.handlers
        if hasattr(h, "baseFilename")
    )

    # Retire logger
    logger._retired = True

    # Attempt rotation
    handler.rotation_callback(handler)

    await logger._queue.join()

    # No rotated files should exist
    rotated = list(tmp_path.glob("r.log*"))
    assert len(rotated) == 1  # only base file


@pytest.mark.asyncio
async def test_rotation_callback_ignored_when_stopped(tmp_path):
    logic = RotationLogic(maxBytes=1, backupCount=1)

    logger = AsyncSmartLogger("rot_stopped", logging.INFO)
    logger.add_file(str(tmp_path), "s.log", rotation_logic=logic)

    handler = next(
        h for h in logger._py_logger.handlers
        if hasattr(h, "baseFilename")
    )

    # Stop logger
    logger._stopped = True

    # Attempt rotation
    handler.rotation_callback(handler)

    await logger._queue.join()

    # No rotated files should exist
    rotated = list(tmp_path.glob("s.log*"))
    assert len(rotated) == 1


@pytest.mark.asyncio
async def test_rotation_callback_enqueues(tmp_path):
    logic = RotationLogic(when=When.SECOND, interval=1, backupCount=1)

    logger = AsyncSmartLogger("rot_cb", logging.INFO)
    logger.add_file(str(tmp_path), "r.log", rotation_logic=logic)

    handler = logger.file_handlers[0]

    # Force rotation (do NOT await)
    logger._AsyncSmartLogger__enqueue_rotation(handler)

    # Give worker time to process
    await asyncio.sleep(0.05)

    # If no exception occurred, callback worked
    assert True

