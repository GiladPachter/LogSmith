# Auto-generated test skeleton for LogSmith

from LogSmith import SmartLogger
from LogSmith import AsyncSmartLogger


def test_smartlogger_logs_critical(tmp_path):
    logdir = tmp_path
    logfile = logdir / "crit.log"

    lg = SmartLogger("crit_test")
    lg.add_file(str(logdir), "crit.log")

    lg.critical("CRITICAL MESSAGE")

    # Flush handlers
    for h in lg._SmartLogger__py_logger.handlers:
        h.flush()

    text = logfile.read_text()

    assert "CRITICAL" in text
    assert "CRITICAL MESSAGE" in text

    lg.destroy()


import pytest

@pytest.mark.asyncio
async def test_asyncsmartlogger_logs_critical(tmp_path):
    logdir = tmp_path
    logfile = logdir / "crit.log"

    lg = AsyncSmartLogger("crit_test_async")
    lg.add_file(str(logdir), "crit.log")

    await lg.a_critical("CRITICAL MESSAGE")
    await lg.flush()

    text = logfile.read_text()

    assert "CRITICAL" in text
    assert "CRITICAL MESSAGE" in text

    await lg.shutdown()
    lg.destroy()
