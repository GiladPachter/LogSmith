import logging

import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.formatter import OutputMode


@pytest.mark.asyncio
async def test_audit_logger_basic(tmp_path):
    # main logger
    main = AsyncSmartLogger("main_audit", logging.INFO)
    main.add_file(str(tmp_path), "main.log", output_mode=OutputMode.PLAIN)

    # audit logger
    audit = AsyncSmartLogger("audit_sink", logging.INFO)
    audit.add_file(str(tmp_path), "audit.log", output_mode=OutputMode.JSON)

    # wire audit
    AsyncSmartLogger._AsyncSmartLogger__audit_enabled = True
    AsyncSmartLogger._AsyncSmartLogger__audit_logger = audit

    await main.a_info("hello-audit")
    await main._queue.join()
    await audit._queue.join()

    text = (tmp_path / "audit.log").read_text(encoding="utf-8").strip()
    assert "hello-audit" in text
    assert "main_audit" in text  # prefixed original logger name
