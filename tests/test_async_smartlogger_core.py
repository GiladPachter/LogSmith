import asyncio
import logging
import os
from pathlib import Path
import pytest

from LogSmith import SmartLogger, AsyncSmartLogger, OptionalRecordFields, LogRecordDetails
from LogSmith.rotation_base import RotationLogic
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler


# ------------------------------------------------------------
# Helper: wait for async logger to flush all work
# ------------------------------------------------------------
async def drain(logger: AsyncSmartLogger):
    await logger.flush()
    await asyncio.sleep(0.05)


# ------------------------------------------------------------
# 1. Worker startup + basic logging
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_async_logger_basic_logging(tmp_path):
    log_dir = str(tmp_path)
    file = "test.log"

    lg = AsyncSmartLogger("async_basic")
    lg.add_file(log_dir, file)

    await lg.a_info("hello world")
    await drain(lg)

    content = Path(tmp_path / file).read_text()
    assert "hello world" in content


# ------------------------------------------------------------
# 2. Rotation scheduling (size-based)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_async_logger_rotation(tmp_path):
    log_dir = str(tmp_path)
    file = "rot.log"

    logic = RotationLogic(maxBytes=1, append_filename_pid=True, append_filename_timestamp=True)

    lg = AsyncSmartLogger("async_rotate")
    lg.add_file(log_dir, file, rotation_logic=logic)

    # Trigger rotation
    await lg.a_info("X")
    await drain(lg)

    rotated = [f for f in os.listdir(log_dir) if f.startswith("rot.log.") and f.endswith(".1")]
    assert rotated, "Rotation did not occur"


# ------------------------------------------------------------
# 3. RAW logging (console + file)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_async_logger_raw(tmp_path):
    log_dir = str(tmp_path)
    file = "raw.log"

    lg = AsyncSmartLogger("async_raw")
    lg.add_file(log_dir, file)

    await lg.a_raw("RAW-LINE", end="")
    await drain(lg)

    content = Path(tmp_path / file).read_text()
    assert "RAW-LINE" in content


# ------------------------------------------------------------
# 4. preserve_colors_in_log_files
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_async_logger_preserve_colors(tmp_path):
    log_dir = str(tmp_path)
    file = "color.log"

    lg = AsyncSmartLogger("async_color")
    lg.add_file(log_dir, file, preserve_colors_in_log_files=True)

    await lg.a_info("\x1b[31mRED\x1b[0m")
    await drain(lg)

    text = Path(tmp_path / file).read_text()
    assert "\x1b[31m" in text  # ANSI preserved


# ------------------------------------------------------------
# 5. Dynamic level registration
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_async_logger_dynamic_level(tmp_path):
    log_dir = str(tmp_path)
    file = "dyn.log"

    lg = AsyncSmartLogger("async_dyn")
    lg.add_file(log_dir, file)

    AsyncSmartLogger.register_level("ALERT", 55)

    await lg.a_alert("ALERT-MSG")
    await drain(lg)

    text = Path(tmp_path / file).read_text()
    assert "ALERT-MSG" in text


# ------------------------------------------------------------
# 6. Retire behavior
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_async_logger_retire(tmp_path):
    lg = AsyncSmartLogger("async_retire")
    lg.retire()

    with pytest.raises(RuntimeError):
        await lg.a_info("should fail")


# ------------------------------------------------------------
# 7. Shutdown behavior
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_async_logger_shutdown(tmp_path):
    log_dir = str(tmp_path)
    file = "shutdown.log"

    lg = AsyncSmartLogger("async_shutdown")
    lg.add_file(log_dir, file)

    await lg.a_info("before shutdown")
    await lg.shutdown()

    # After shutdown, logging must fail
    with pytest.raises(RuntimeError):
        await lg.a_info("after shutdown")


# ------------------------------------------------------------
# 8. Audit mode
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_async_logger_audit(tmp_path):
    log_dir = str(tmp_path)
    file = "audit.log"

    await AsyncSmartLogger.audit_everything(
        log_dir=log_dir,
        logfile_name=file,
    )

    lg = AsyncSmartLogger("audit_test")
    await lg.a_info("AUDIT-MSG")
    await drain(lg)

    text = Path(tmp_path / file).read_text()
    assert "[audit_test]:" in text or "audit_test" in text

    await AsyncSmartLogger.terminate_auditing()


# ------------------------------------------------------------
# 9. Exception info + stack info
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_async_logger_exc_and_stack(tmp_path):
    log_dir = str(tmp_path)
    file = "exc.log"

    lg = AsyncSmartLogger("async_exc")

    orf = OptionalRecordFields(
        exc_info=True,
        stack_info=True,
    )
    details = LogRecordDetails(
        optional_record_fields=orf,
    )

    lg.add_file(log_dir, file, log_record_details=details)

    # noinspection PyBroadException
    try:
        raise ValueError("boom")
    except Exception:
        await lg.a_error("ERR", exc_info=True, stack_info=True)

    await drain(lg)

    text = Path(tmp_path / file).read_text()
    assert "ValueError" in text
    assert "boom" in text
    assert "File" in text  # stack trace


# ------------------------------------------------------------
# 10. Profiling
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_async_logger_profiling(tmp_path):
    log_dir = str(tmp_path)
    file = "prof.log"

    lg = AsyncSmartLogger("async_prof")
    lg.enable_profiling(True)
    lg.add_file(log_dir, file)

    for _ in range(5):
        await lg.a_info("msg")

    await drain(lg)

    details = lg.get_profiling_details()
    assert "Avg" in details
    assert "Total log events" in details
