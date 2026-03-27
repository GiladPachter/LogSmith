# tests/async_logger/test_async_audit_forwarding.py
import json
import asyncio
import logging
from LogSmith.async_smartlogger import AsyncSmartLogger

import pytest


import json
import asyncio
import logging
import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger


import json
import asyncio
import logging
import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger


@pytest.mark.asyncio
async def test_audit_forwarding(tmp_path):
    logger = AsyncSmartLogger("main", logging.INFO)
    logger.add_file(str(tmp_path), "main.json", output_mode="json")

    await logger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.json",
    )

    await logger.a_info("hello", foo=42)
    await asyncio.sleep(0.05)

    text = (tmp_path / "audit.json").read_text(encoding="utf-8").strip()
    lines = text.splitlines()
    assert len(lines) >= 1

    prefix, log_entry_text = lines[0].split("]: ", 1)
    prefix = prefix + "]"

    assert prefix == "[main]"
    assert "hello" in log_entry_text
    assert "foo=42" in log_entry_text

    # IMPORTANT: reset global audit state for the next test
    await AsyncSmartLogger.terminate_auditing()
