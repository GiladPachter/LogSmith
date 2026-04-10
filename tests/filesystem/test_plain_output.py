import pytest

from pathlib import Path

from LogSmith import SmartLogger
from LogSmith import AsyncSmartLogger
from LogSmith import RotationLogic
from LogSmith import LogRecordDetails, OptionalRecordFields


def test_plain_output(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    logger = SmartLogger("fs_plain", level=SmartLogger.levels()["INFO"])
    logger.add_file(log_dir=str(log_dir), logfile_name="app.log", rotation_logic=RotationLogic())

    logger.info("hello", user="gilad")

    content = (log_dir / "app.log").read_text(encoding="utf-8")
    assert "hello" in content
    assert "{user='gilad'}" in content


@pytest.mark.asyncio
async def test_smartlogger_writes_taskname_excinfo_stackinfo(tmp_path):
    log_file = tmp_path / "test.log"

    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(
            task_name=True,
            exc_info=True,
            stack_info=True,
        ),
        message_parts_order=[
            "level",
            "task_name",
        ],
    )

    logger = AsyncSmartLogger("test_smartlogger_fields")
    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="test.log",
        log_record_details=details,
    )

    # Generate an exception to test exc_info
    try:
        raise ValueError("boom")
    except Exception:
        await logger.a_info(
            "testing fields",
            exc_info=True,
            stack_info=True,
            extra={"taskName": "unit-test-task"},
        )

    await logger.flush()
    logger.destroy()

    # Read file
    text = log_file.read_text(encoding="utf-8")

    # Assertions
    assert "unit-test-task" in text          # task_name
    assert "ValueError: boom" in text        # exc_info
    assert "Stack (most recent call last" in text or "File" in text  # stack_info


def test_smartlogger_add_file_without_log_record_details(tmp_path):
    log_file = tmp_path / "no_details.log"

    logger = SmartLogger("test_no_details")

    # Call add_file WITHOUT log_record_details
    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="no_details.log",
        # log_record_details omitted intentionally
    )

    # Write a simple log entry
    logger.info("hello world")
    # logger.flush()
    logger.destroy()

    # Verify file exists
    assert log_file.exists()

    # Verify content was written
    text = log_file.read_text()
    assert "hello world" in text

    # Default formatter includes timestamp and level
    assert "INFO" in text
