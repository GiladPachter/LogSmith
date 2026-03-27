import pytest
import asyncio
from pathlib import Path
import logging

from LogSmith.smartlogger import SmartLogger
from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.formatter import LogRecordDetails, OptionalRecordFields


# ------------------------------------------------------------
# Helper: read file content
# ------------------------------------------------------------
def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


# ------------------------------------------------------------
# 1. Basic INFO message parity
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_basic_info_parity(tmp_path):
    sync_file = tmp_path / "sync.log"
    async_file = tmp_path / "async.log"

    sync = SmartLogger("sync")
    sync.add_file(log_dir=str(tmp_path), logfile_name="sync.log")

    async_lg = AsyncSmartLogger("async")
    async_lg.add_file(log_dir=str(tmp_path), logfile_name="async.log")

    sync.info("hello world")
    await async_lg.a_info("hello world")
    await async_lg.flush()

    assert read(sync_file).endswith("hello world")
    assert read(async_file).endswith("hello world")


# ------------------------------------------------------------
# 2. Extras parity
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_extras_parity(tmp_path):
    sync_file = tmp_path / "sync.log"
    async_file = tmp_path / "async.log"

    sync = SmartLogger("sync2")
    sync.add_file(log_dir=str(tmp_path), logfile_name="sync.log")

    async_lg = AsyncSmartLogger("async2")
    async_lg.add_file(log_dir=str(tmp_path), logfile_name="async.log")

    sync.info("msg", user="gilad", x=5)
    await async_lg.a_info("msg", user="gilad", x=5)
    await async_lg.flush()

    s = read(sync_file)
    a = read(async_file)

    assert "{user='gilad', x=5}" in s or "{user='gilad', x=5}" in a
    assert s.endswith("msg {user='gilad', x=5}") and a.endswith("msg {user='gilad', x=5}")


# ------------------------------------------------------------
# 3. ANSI sanitization parity
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_ansi_sanitization_parity(tmp_path):
    sync_file = tmp_path / "sync.log"
    async_file = tmp_path / "async.log"

    sync = SmartLogger("sync3")
    sync.add_file(log_dir=str(tmp_path), logfile_name="sync.log")

    async_lg = AsyncSmartLogger("async3")
    async_lg.add_file(log_dir=str(tmp_path), logfile_name="async.log")

    colored = "\x1b[31mRED\x1b[0m"

    sync.info(colored)
    await async_lg.a_info(colored)
    await async_lg.flush()

    assert "RED" in read(sync_file)
    assert "RED" in read(async_file)
    assert "\x1b" not in read(sync_file)
    assert "\x1b" not in read(async_file)


# ------------------------------------------------------------
# 4. Preserve colors parity
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_preserve_colors_parity(tmp_path):
    sync_file = tmp_path / "sync.log"
    async_file = tmp_path / "async.log"

    sync = SmartLogger("sync4")
    sync.add_file(log_dir=str(tmp_path), logfile_name="sync.log",
                  preserve_colors_in_log_files=True)

    async_lg = AsyncSmartLogger("async4")
    async_lg.add_file(log_dir=str(tmp_path), logfile_name="async.log",
                      preserve_colors_in_log_files=True)

    colored = "\x1b[32mGREEN\x1b[0m"

    sync.info(colored)
    await async_lg.a_info(colored)
    await async_lg.flush()

    assert "\x1b[32m" in read(sync_file)
    assert "\x1b[32m" in read(async_file)


# ------------------------------------------------------------
# 5. LogRecordDetails parity
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_logrecorddetails_parity(tmp_path):
    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(file_name=True, lineno=True),
        message_parts_order=["level", "file_name", "lineno"],
    )

    sync_file = tmp_path / "sync.log"
    async_file = tmp_path / "async.log"

    sync = SmartLogger("sync5")
    sync.add_file(log_dir=str(tmp_path), logfile_name="sync.log",
                  log_record_details=details)

    async_lg = AsyncSmartLogger("async5")
    async_lg.add_file(log_dir=str(tmp_path), logfile_name="async.log",
                      log_record_details=details)

    sync.info("hello")
    await async_lg.a_info("hello")
    await async_lg.flush()

    s = read(sync_file)
    a = read(async_file)

    assert "hello" in s and "hello" in a
    assert "sync5" not in s  # logger_name not enabled
    assert "async5" not in a


# ------------------------------------------------------------
# 6. exc_info parity
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_exc_info_parity(tmp_path):
    sync_file = tmp_path / "sync.log"
    async_file = tmp_path / "async.log"

    orf = OptionalRecordFields(exc_info=True)
    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=None,  # allowed in diagnostics-only mode
    )

    sync = SmartLogger("sync6")
    sync.add_file(log_dir=str(tmp_path), logfile_name="sync.log", log_record_details=details)

    async_lg = AsyncSmartLogger("async6")
    async_lg.add_file(log_dir=str(tmp_path), logfile_name="async.log", log_record_details=details)

    try:
        raise RuntimeError("boom")
    except Exception:
        sync.error("err", exc_info=True)
        await async_lg.a_error("err", exc_info=True)
        await async_lg.flush()

    s = read(sync_file)
    a = read(async_file)

    assert "RuntimeError" in s
    assert "RuntimeError" in a


# ------------------------------------------------------------
# 7. stack_info parity
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_stack_info_parity(tmp_path):
    sync_file = tmp_path / "sync.log"
    async_file = tmp_path / "async.log"

    sync = SmartLogger("sync7")
    sync.add_file(log_dir=str(tmp_path), logfile_name="sync.log")

    async_lg = AsyncSmartLogger("async7")
    async_lg.add_file(log_dir=str(tmp_path), logfile_name="async.log")

    sync.info("stack", stack_info=True)
    await async_lg.a_info("stack", stack_info=True)
    await async_lg.flush()

    s = read(sync_file)
    a = read(async_file)

    assert "stack" in s  # stack trace present
    assert "stack" in a


# ------------------------------------------------------------
# 8. get_record parity
# ------------------------------------------------------------
def test_get_record_parity():
    sync = SmartLogger("sync8")
    async_lg = AsyncSmartLogger("async8")

    # s = sync.get_record(exc_info=False, stack_info=False)
    s = sync.get_record()
    a = async_lg.get_record(exc_info=False, stack_info=False)

    assert isinstance(s.timestamp, str)
    assert isinstance(a.timestamp, str)

    assert s.file_name is not None
    assert a.file_name is not None

    assert s.thread_id is not None
    assert a.thread_id is not None
