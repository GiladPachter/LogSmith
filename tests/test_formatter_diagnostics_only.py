import logging

import pytest

from LogSmith import SmartLogger, LogRecordDetails, OptionalRecordFields, AsyncSmartLogger, OutputMode


def test_formatter_diagnostics_only(tmp_path):
    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(
            exc_info=True,
            stack_info=True,
        ),
        message_parts_order=None,
    )

    logger = SmartLogger("diag", logging.INFO)
    logger.add_file(str(tmp_path), "d.log", log_record_details=details)

    try:
        raise RuntimeError("boom")
    except Exception:
        logger.error("x", exc_info=True, stack_info=True)

    text = (tmp_path / "d.log").read_text()
    assert "RuntimeError: boom" in text




@pytest.mark.asyncio
async def test_formatter_exception_does_not_crash(tmp_path, monkeypatch):
    logger = AsyncSmartLogger("fmt_error", logging.INFO)
    logger.add_file(str(tmp_path), "fe.log", output_mode=OutputMode.JSON)

    # grab the handler and break its formatter
    handler = next(h for h in logger._py_logger.handlers if hasattr(h, "baseFilename"))

    def bad_format(record):
        raise ValueError("boom")

    monkeypatch.setattr(handler.formatter, "format", bad_format)

    # should not raise, even though formatter explodes
    await logger.a_info("will-not-format")
    await logger._queue.join()

    # file may be empty or partial, but process must survive
    assert (tmp_path / "fe.log").exists()
