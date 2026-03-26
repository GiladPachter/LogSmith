import pytest
from pathlib import Path
from LogSmith.async_smartlogger import AsyncSmartLogger


@pytest.mark.asyncio
async def test_metadata_extra_and_fields_merge(tmp_path):
    logger = AsyncSmartLogger("meta_merge")
    logger.add_file(log_dir=str(tmp_path))

    # Send metadata via kwargs (fields) and via extra
    await logger.a_info(
        "hello",
        user="gilad",
        request_id=123,
        extra={"session": "abc"},
    )

    await logger.flush()
    await logger.shutdown()

    # Read file
    file_path = Path(tmp_path) / "meta_merge.log"
    text = file_path.read_text()

    # Both fields and extra must appear
    assert "gilad" in text
    assert "123" in text
    assert "abc" in text


@pytest.mark.asyncio
async def test_metadata_audit_prefix(tmp_path):
    # Enable auditing
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    logger = AsyncSmartLogger("app_logger")
    logger.add_file(log_dir=str(tmp_path))

    await logger.a_info("hello audit")
    await logger.flush()

    # Shutdown audit logger
    await AsyncSmartLogger.terminate_auditing()

    # Read audit file
    audit_file = Path(tmp_path) / "audit.log"
    text = audit_file.read_text()

    # Audit prefix must appear
    assert "app_logger" in text
    assert "hello audit" in text


@pytest.mark.asyncio
async def test_metadata_preserve_colors_in_file(tmp_path):
    logger = AsyncSmartLogger("meta_color")
    logger.add_file(log_dir=str(tmp_path), preserve_colors_in_log_files=True)

    msg = "\x1b[31mRED\x1b[0m test"
    await logger.a_info(msg)
    await logger.flush()
    await logger.shutdown()

    file_path = Path(tmp_path) / "meta_color.log"
    text = file_path.read_text()

    # ANSI must be preserved
    assert "\x1b[31m" in text
    assert "RED" in text


@pytest.mark.asyncio
async def test_metadata_strip_colors_in_file(tmp_path):
    logger = AsyncSmartLogger("meta_strip")
    logger.add_file(log_dir=str(tmp_path), preserve_colors_in_log_files=False)

    msg = "\x1b[32mGREEN\x1b[0m test"
    await logger.a_info(msg)
    await logger.flush()
    await logger.shutdown()

    file_path = Path(tmp_path) / "meta_strip.log"
    text = file_path.read_text()

    # ANSI must be stripped
    assert "GREEN" in text
    assert "\x1b[32m" not in text


@pytest.mark.asyncio
async def test_metadata_audited_logger_name_override(tmp_path):
    # Enable auditing
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit2.log",
    )

    logger = AsyncSmartLogger("source_logger")
    logger.add_file(log_dir=str(tmp_path))

    # This will inject "__audited_logger_name__" into extra
    await logger.a_info("audit override test")
    await logger.flush()

    await AsyncSmartLogger.terminate_auditing()

    audit_file = Path(tmp_path) / "audit2.log"
    text = audit_file.read_text()

    # The audit prefix must use the original logger name
    assert "source_logger" in text
    assert "audit override test" in text
