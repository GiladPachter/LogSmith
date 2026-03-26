# tests/async/test_async_smartlogger_audit.py
import asyncio
import pytest
from pathlib import Path

from LogSmith.async_smartlogger import AsyncSmartLogger

@pytest.mark.asyncio
async def test_audit_pipeline(tmp_path):
    log_dir = str(tmp_path)
    audit_file = "audit.log"

    await AsyncSmartLogger.audit_everything(
        log_dir=log_dir,
        logfile_name=audit_file,
    )

    lg = AsyncSmartLogger("userlog")
    lg.add_file(log_dir, "user.log")

    await lg.a_info("HELLO")
    await lg.flush()
    await asyncio.sleep(0.05)

    text = Path(tmp_path / audit_file).read_text()
    assert "userlog" in text
    assert "HELLO" in text

    info = AsyncSmartLogger.audit_handler_info()
    assert info["kind"] == "file"
    assert info["path"].endswith(audit_file)

    await AsyncSmartLogger.terminate_auditing()
    assert AsyncSmartLogger.audit_handler_info() is None
