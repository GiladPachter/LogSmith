import logging
from LogSmith import SmartLogger, LogRecordDetails, OptionalRecordFields

def test_optional_fields_and_order(tmp_path):
    # Enable several inline optional fields
    orf = OptionalRecordFields(
        logger_name=True,
        file_name=True,
        lineno=True,
        func_name=True,
        thread_id=True,
    )

    # message_parts_order must include ALL enabled fields + "level"
    mpo = [
        "level",
        "logger_name",
        "file_name",
        "lineno",
        "func_name",
        "thread_id",
    ]

    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=mpo,
    )

    logger = SmartLogger("fmt", logging.INFO)
    logger.add_file(str(tmp_path), "f.log", log_record_details=details)

    logger.info("hello")
    text = (tmp_path / "f.log").read_text()

    # Enabled fields must appear
    assert "fmt" in text                  # logger_name
    assert "hello" in text                # message
    assert "L=" in text                   # lineno
    assert "INFO" in text                 # level
    assert "test_optional_fields" in text or "<module>" in text  # func_name
