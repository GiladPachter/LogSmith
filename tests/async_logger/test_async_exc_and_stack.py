import pytest
import logging
from LogSmith import AsyncSmartLogger, OptionalRecordFields, LogRecordDetails


@pytest.mark.asyncio
async def test_async_exc_info_and_stack_info(tmp_path):
    logger = AsyncSmartLogger("excstack", logging.INFO)
    logger.add_file(str(tmp_path), "e.log", log_record_details=LogRecordDetails(
        datefmt="%Y-%m-%d %H:%M:%S",
        separator="|",
        optional_record_fields=OptionalRecordFields(
            exc_info=True,
            stack_info=True,
        ),
    ))

    try:
        raise ValueError("boom")
    except Exception:
        await logger.a_error("with exc", exc_info=True, stack_info=True)

    # await logger._queue.join()
    await logger.flush()

    text = (tmp_path / "e.log").read_text(encoding="utf-8")
    assert "ValueError: boom" in text
    assert "Stack (most recent call last)" in text or "Traceback" in text
