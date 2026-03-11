import logging
from LogSmith import SmartLogger, LogRecordDetails, OptionalRecordFields

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
