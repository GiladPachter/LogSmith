import logging

import pytest


@pytest.mark.asyncio
async def test_worker_survives_handler_exception(clean_async_logger, tmp_path):
    logger = clean_async_logger
    logger.add_file(str(tmp_path), "x.log")

    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    def bad_emit(record):
        raise RuntimeError("boom")

    handler.emit = bad_emit

    before = logger.messages_processed()

    # This one will fail inside the handler
    await logger.a_info("hello")
    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    after_fail = logger.messages_processed()
    # Failed log is not counted
    assert after_fail == before

    # Restore a working emit
    original_emit = logging.FileHandler.emit
    handler.emit = original_emit.__get__(handler, type(handler))

    # This one should succeed
    await logger.a_info("world")
    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    after_success = logger.messages_processed()
    assert after_success == before + 1

    content = (tmp_path / "x.log").read_text()
    assert "world" in content

    logger.destroy()


@pytest.mark.asyncio
async def test_worker_survives_formatter_exception(clean_async_logger, tmp_path, monkeypatch):
    logger = clean_async_logger

    logger.add_file(str(tmp_path), "x.log")

    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    class BadFormatter(logging.Formatter):
        def format(self, record):
            raise RuntimeError("format fail")

    handler.setFormatter(BadFormatter())

    # Silence stdlib logging's "Logging error" diagnostics
    monkeypatch.setattr(logging, "raiseExceptions", False)

    before = logger.messages_processed()

    await logger.a_info("hello")
    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    after = logger.messages_processed()

    assert after == before + 1

    logger.destroy()


@pytest.mark.asyncio
async def test_worker_preserves_message_order(clean_async_logger, tmp_path):
    logger = clean_async_logger

    logger.add_file(str(tmp_path), "x.log")

    for i in range(5):
        await logger.a_info(f"msg-{i}")

    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    content = (tmp_path / "x.log").read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]

    # Extract only the message body (after the last "•")
    bodies = [line.split("•")[-1].strip() for line in lines]

    assert bodies == [f"msg-{i}" for i in range(5)]

    logger.destroy()


@pytest.mark.asyncio
async def test_worker_drains_queue(clean_async_logger, tmp_path):
    logger = clean_async_logger

    logger.add_file(str(tmp_path), "x.log")

    for i in range(50):
        await logger.a_info("hello")

    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    assert logger.queue_size == 0

    logger.destroy()


@pytest.mark.asyncio
async def test_worker_handles_raw_write(clean_async_logger, tmp_path):
    logger = clean_async_logger

    logger.add_file(str(tmp_path), "x.log")

    await logger.a_raw("raw-text")
    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    content = (tmp_path / "x.log").read_text()
    assert "raw-text" in content

    logger.destroy()


@pytest.mark.asyncio
async def test_worker_survives_raw_write_exception(clean_async_logger, tmp_path):
    logger = clean_async_logger

    logger.add_file(str(tmp_path), "x.log")
    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    def bad_write(text):
        raise RuntimeError("raw fail")

    handler.stream.write = bad_write

    before = logger.messages_processed()

    # RAW write fails
    await logger.a_raw("hello")
    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    after_fail = logger.messages_processed()

    # RAW writes are never counted
    assert after_fail == before

    # Restore working write
    handler.stream.write = lambda text: None

    # Now test that the worker is still alive by sending a NORMAL log
    await logger.a_info("world")
    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    after_success = logger.messages_processed()

    # Normal logs ARE counted
    assert after_success == before + 1

    logger.destroy()


@pytest.mark.asyncio
async def test_worker_handles_large_queue(clean_async_logger, tmp_path):
    logger = clean_async_logger

    logger.add_file(str(tmp_path), "x.log")

    for i in range(2000):
        await logger.a_info("spam")

    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    assert logger.messages_processed() >= 2000

    logger.destroy()


@pytest.mark.asyncio
async def test_worker_stays_alive(clean_async_logger, tmp_path):
    logger = clean_async_logger

    logger.add_file(str(tmp_path), "x.log")

    await logger.a_info("first")
    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    before = logger.messages_processed()

    await logger.a_info("second")
    # await logger.__queue.join()
    await logger._AsyncSmartLogger__queue.join()    # accessing private member. do not use outside of test suite

    after = logger.messages_processed()

    assert after == before + 1

    logger.destroy()


@pytest.mark.asyncio
async def test_worker_swallows_exceptions(tmp_path, monkeypatch):
    from LogSmith.async_smartlogger import AsyncSmartLogger

    lg = AsyncSmartLogger("err_test")
    lg.add_file(str(tmp_path), "exp.log")

    # Force __process_log to raise
    monkeypatch.setattr(
        lg,
        "_AsyncSmartLogger__process_log",
        lambda payload: (_ for _ in ()).throw(Exception("boom"))
    )

    await lg.a_info("A")
    await lg.flush()

    # Worker should not crash
    assert True

    lg.destroy()


@pytest.mark.asyncio
async def test_worker_exits_on_sentinel(tmp_path):
    from LogSmith.async_smartlogger import AsyncSmartLogger, AsyncOp
    import asyncio

    lg = AsyncSmartLogger("exit_test")
    lg.add_file(str(tmp_path), "exp.log")

    class Dummy:
        def __init__(self, op):
            self.op = op
            self.payload = None

    await lg._AsyncSmartLogger__queue.put(Dummy(AsyncOp.SENTINEL))

    await asyncio.sleep(0.1)

    for task in lg._AsyncSmartLogger__worker_tasks:
        assert task.done()

    lg.destroy()
