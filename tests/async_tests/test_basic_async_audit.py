import logging

import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.formatter import OutputMode, LogRecordDetails


@pytest.mark.asyncio
async def test_audit_logger_basic(tmp_path):
    main = AsyncSmartLogger("main_audit", logging.INFO)
    main.add_file(str(tmp_path), "main.log", output_mode=OutputMode.PLAIN)

    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
        rotation_logic=None,
        details=LogRecordDetails(),
        # NDJSON_output=False (or True, depending on what you want)
    )

    await main.a_info("hello-audit")
    await main._AsyncSmartLogger__queue.join()
    await AsyncSmartLogger._AsyncSmartLogger__audit_logger._AsyncSmartLogger__queue.join()

    text = (tmp_path / "audit.log").read_text(encoding="utf-8").strip()
    assert "hello-audit" in text
    assert "main_audit" in text
