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
    # main logger
    logger = AsyncSmartLogger("main", logging.INFO)
    logger.add_file(str(tmp_path), "main.json", output_mode="json")

    # enable auditing (creates internal audit logger)
    await logger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.json",
    )

    await logger.a_info("hello", foo=42)
    await asyncio.sleep(0.05)

    # read audit output
    text = (tmp_path / "audit.json").read_text(encoding="utf-8").strip()
    lines = text.splitlines()
    assert len(lines) >= 1

    # auditing format: <AUDITED_LOGGER_NAME> : <UNMANIPULATED_LOG_ENTRY>
    # prefix, json_part = lines[0].split(" : ", 1)
    prefix, log_entry_text = lines[0].split(" : ", 1)

    # prefix must be the audited logger name
    assert prefix == "main"

    # # parse the JSON part
    # data = json.loads(json_part)

    # assert data["fields"]["foo"] == 42
    # assert data["message"] == "hello"
    assert "hello" in log_entry_text
    assert 'foo=42' in log_entry_text
