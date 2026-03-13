import pytest
import logging
from LogSmith import AsyncSmartLogger, RotationLogic, When


@pytest.mark.asyncio
async def test_async_stream_reopen_rotating_when_stream_none(tmp_path):
    """
    If a rotating handler's stream is None, AsyncSmartLogger should reopen it
    before emitting a record.
    """
    logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        backupCount=1,
    )

    logger = AsyncSmartLogger("reopen_rot", logging.INFO)
    logger.add_file(str(tmp_path), "r.log", rotation_logic=logic)

    handler = next(
        h for h in logger._py_logger.handlers
        if hasattr(h, "baseFilename")
    )

    assert hasattr(handler, "_open")

    # simulate lost stream
    handler.stream = None

    await logger.a_info("hello")
    await logger._queue.join()

    assert handler.stream is not None
    assert not handler.stream.closed


@pytest.mark.asyncio
async def test_async_stream_reopen_json_when_stream_none(tmp_path):
    """
    For JSON output with a rotating handler, if stream is None,
    AsyncSmartLogger should reopen it and still write JSON.
    """
    logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        backupCount=1,
    )

    logger = AsyncSmartLogger("reopen_json", logging.INFO)
    logger.add_file(
        str(tmp_path),
        "j.log",
        rotation_logic=logic,
        output_mode="json",  # uses StructuredJSONFormatter
    )

    handler = next(
        h for h in logger._py_logger.handlers
        if hasattr(h, "baseFilename")
    )

    assert hasattr(handler, "_open")

    # simulate lost stream
    handler.stream = None

    await logger.a_info("hello", extra={"foo": "bar"})
    await logger._queue.join()

    assert handler.stream is not None
    assert not handler.stream.closed

    text = (tmp_path / "j.log").read_text(encoding="utf=8").strip()
    # basic sanity: JSON line with our field present
    assert "hello" in text
    assert "foo" in text
