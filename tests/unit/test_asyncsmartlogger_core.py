import json
from pathlib import Path

import pytest

from LogSmith import AsyncSmartLogger, OutputMode


@pytest.mark.asyncio
async def test_async_console_logging(capsys):
    levels = AsyncSmartLogger.levels()
    logger = AsyncSmartLogger("async.console", level=levels["TRACE"])
    logger.add_console()

    await logger.a_trace("trace message")
    await logger.a_debug("debug message")
    await logger.a_info("info message")
    await logger.flush()

    await logger.flush()

    out = capsys.readouterr().out
    assert "trace message" in out
    assert "debug message" in out
    assert "info message" in out


@pytest.mark.asyncio
async def test_async_file_logging_ndjson(tmp_path: Path):
    levels = AsyncSmartLogger.levels()
    logger = AsyncSmartLogger("async.file", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="async.ndjson",
        output_mode=OutputMode.NDJSON,
    )

    await logger.a_info("User login", username="Gilad")
    await logger.a_warning("Something odd", code=123)
    await logger.flush()

    logfile = log_dir / "async.ndjson"
    assert logfile.exists()

    lines = logfile.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])

    assert first["level"] == "INFO"
    assert first["message"] == "User login"
    assert first["fields"]["username"] == "Gilad"

    assert second["level"] == "WARNING"
    assert second["fields"]["code"] == 123


@pytest.mark.asyncio
async def test_async_ordering_guarantee(tmp_path: Path):
    levels = AsyncSmartLogger.levels()
    logger = AsyncSmartLogger("async.order", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="order.ndjson",
        output_mode=OutputMode.NDJSON,
    )

    for i in range(50):
        await logger.a_info("msg", index=i)

    await logger.flush()

    logfile = log_dir / "order.ndjson"
    lines = logfile.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 50

    indices = [json.loads(line)["fields"]["index"] for line in lines]
    assert indices == list(range(50))
