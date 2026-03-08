import asyncio
import logging
import pytest
from pathlib import Path

from LogSmith.async_smartlogger import AsyncSmartLogger


@pytest.mark.asyncio
async def test_audit_logger_receives_mirrored_logs(tmp_path):
    """
    When audit mode is enabled, logs from one logger should be mirrored
    into the audit logger, unless the audit logger is the source.
    """
    # Primary logger
    main_logger = AsyncSmartLogger("test_audit_main", logging.INFO)
    main_logger.add_file(str(tmp_path), "main.log")

    # Audit logger
    audit_logger = AsyncSmartLogger("test_audit_audit", logging.INFO)
    audit_logger.add_file(str(tmp_path), "audit.log")

    # Enable audit mode
    AsyncSmartLogger._AsyncSmartLogger__audit_enabled = True
    AsyncSmartLogger._AsyncSmartLogger__audit_logger = audit_logger

    await main_logger.a_info("hello audit")
    await main_logger._queue.join()
    await audit_logger._queue.join()

    # Audit logger should have received the mirrored message
    audit_text = (tmp_path / "audit.log").read_text()
    assert "hello audit" in audit_text

    # Cleanup audit mode
    AsyncSmartLogger._AsyncSmartLogger__audit_enabled = False
    AsyncSmartLogger._AsyncSmartLogger__audit_logger = None


@pytest.mark.asyncio
async def test_audit_logger_does_not_recurse(tmp_path):
    """
    The audit logger must NOT audit its own logs.
    """
    audit_logger = AsyncSmartLogger("test_audit_no_recurse", logging.INFO)
    audit_logger.add_file(str(tmp_path), "audit2.log")

    # Enable audit mode
    AsyncSmartLogger._AsyncSmartLogger__audit_enabled = True
    AsyncSmartLogger._AsyncSmartLogger__audit_logger = audit_logger

    # Emit from the audit logger itself
    await audit_logger.a_info("self-audit")
    await audit_logger._queue.join()

    text = (tmp_path / "audit2.log").read_text()

    # Should appear only once — no recursion
    assert text.count("self-audit") == 1

    # Cleanup
    AsyncSmartLogger._AsyncSmartLogger__audit_enabled = False
    AsyncSmartLogger._AsyncSmartLogger__audit_logger = None


# import pytest
# import logging
#
# from LogSmith.async_smartlogger import AsyncSmartLogger

@pytest.mark.asyncio
async def test_audit_handler_metadata(tmp_path):
    audit_logger = AsyncSmartLogger("test_audit_meta", logging.INFO)
    audit_logger.add_file(str(tmp_path), "audit_meta.log")

    # Enable audit mode
    AsyncSmartLogger._AsyncSmartLogger__audit_enabled = True
    AsyncSmartLogger._AsyncSmartLogger__audit_logger = audit_logger
    AsyncSmartLogger._AsyncSmartLogger__audit_handler = audit_logger._py_logger.handlers[0]

    meta = AsyncSmartLogger.audit_handler_info()

    assert meta is not None
    assert meta["kind"] == "file"
    assert str(meta["path"]).endswith("audit_meta.log")

    # Cleanup
    AsyncSmartLogger._AsyncSmartLogger__audit_enabled = False
    AsyncSmartLogger._AsyncSmartLogger__audit_logger = None
    AsyncSmartLogger._AsyncSmartLogger__audit_handler = None

