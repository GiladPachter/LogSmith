import io
import logging
import os
import time

import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.formatter import (
    StructuredPlainFormatter,
    StructuredColorFormatter,
    StructuredJSONFormatter,
    StructuredNDJSONFormatter,
    LogRecordDetails, OptionalRecordFields,
)
from LogSmith.rotation_base import RotationLogic, When
from LogSmith.colors import CPrint
from LogSmith.async_rotation import Async_TimedSizedRotatingFileHandler


# ============================================================
# Corrected MockRotatingHandler
# ============================================================


class MockRotatingHandler(Async_TimedSizedRotatingFileHandler):
    def __init__(self, formatter=None):
        super().__init__(
            filename="mock.log",
            when=None,
            interval=1,
            timestamp=None,
            max_bytes=0,
            backup_count=0,
            expiration_rule=None,
            encoding="utf-8",
            large_entry_behavior=None,
        )
        self.stream = io.StringIO()
        self.formatter = formatter or logging.Formatter("%(message)s")
        self.rotation_callback = None
        self.resolved_path = "mock.log"

    def _open(self):
        self.stream = io.StringIO()
        return self.stream

    def perform_rotation(self):
        pass


# ============================================================
# 1. JSON / NDJSON / COLOR / PLAIN formatter branches
# ============================================================

@pytest.mark.asyncio
async def test_json_formatter_branch(tmp_path):
    logger = AsyncSmartLogger("json-branch")
    details = LogRecordDetails()
    handler = MockRotatingHandler(
        formatter=StructuredJSONFormatter(details, indent=None)
    )
    logger._AsyncSmartLogger__py_logger.addHandler(handler)

    await logger.a_info("json msg")
    await logger.flush()

    text = handler.stream.getvalue()
    assert "json msg" in text
    assert text.strip().startswith("{")


@pytest.mark.asyncio
async def test_ndjson_formatter_branch(tmp_path):
    logger = AsyncSmartLogger("ndjson-branch")
    details = LogRecordDetails()
    handler = MockRotatingHandler(
        formatter=StructuredNDJSONFormatter(details)
    )
    logger._AsyncSmartLogger__py_logger.addHandler(handler)

    await logger.a_info("ndjson msg")
    await logger.flush()

    text = handler.stream.getvalue()
    assert "ndjson msg" in text
    assert "\n" in text


@pytest.mark.asyncio
async def test_color_formatter_branch(tmp_path):
    logger = AsyncSmartLogger("color-branch")
    details = LogRecordDetails()
    handler = MockRotatingHandler(
        formatter=StructuredColorFormatter(details)
    )
    logger._AsyncSmartLogger__py_logger.addHandler(handler)

    # Use CPrint explicitly so the import is meaningful
    sample = CPrint.colorize("x", fg=CPrint.FG.RED)
    assert "\x1b[" in sample  # ensure ANSI was generated

    await logger.a_info("color msg")
    await logger.flush()

    text = handler.stream.getvalue()
    assert "color msg" in text


@pytest.mark.asyncio
async def test_plain_formatter_branch(tmp_path):
    logger = AsyncSmartLogger("plain-branch")
    details = LogRecordDetails()
    handler = MockRotatingHandler(
        formatter=StructuredPlainFormatter(details)
    )
    logger._AsyncSmartLogger__py_logger.addHandler(handler)

    await logger.a_info("plain msg")
    await logger.flush()

    text = handler.stream.getvalue()
    assert "plain msg" in text


# ============================================================
# 2. Handler reopen logic: stream is None / closed
# ============================================================

@pytest.mark.asyncio
async def test_handler_reopen_when_stream_none(tmp_path):
    logger = AsyncSmartLogger("reopen-none")

    # Use safe formatter to avoid JSON exceptions
    handler = MockRotatingHandler(
        formatter=logging.Formatter("%(message)s")
    )
    logger._AsyncSmartLogger__py_logger.addHandler(handler)

    handler.stream = None  # force reopen

    await logger.a_info("reopen msg")
    await logger.flush()

    text = handler.stream.getvalue()
    assert "reopen msg" in text


@pytest.mark.asyncio
async def test_handler_reopen_when_stream_closed(tmp_path):
    logger = AsyncSmartLogger("reopen-closed")

    handler = MockRotatingHandler(
        formatter=logging.Formatter("%(message)s")
    )
    logger._AsyncSmartLogger__py_logger.addHandler(handler)

    handler.stream.close()
    handler.stream = handler.stream  # closed but not None

    await logger.a_info("closed msg")
    await logger.flush()

    text = handler.stream.getvalue()
    assert "closed msg" in text


# ============================================================
# 3. Profiling: steady vs spike + rotation profiling
# ============================================================

@pytest.mark.asyncio
async def test_profiling_steady_and_spike_and_rotation():
    logger = AsyncSmartLogger("profile-rot")
    logger.enable_profiling(True)

    details = LogRecordDetails()
    handler = MockRotatingHandler(
        formatter=StructuredPlainFormatter(details)
    )
    logger._AsyncSmartLogger__py_logger.addHandler(handler)

    # steady logs
    for _ in range(5):
        await logger.a_info("steady")
    await logger.flush()

    # spike logs
    original_emit = handler.emit

    def slow_emit(record):
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < 0.001:
            pass
        original_emit(record)

    handler.emit = slow_emit

    for _ in range(3):
        await logger.a_info("spike")
    await logger.flush()

    # rotation profiling
    async def do_rotation():
        payload = {"handler": handler}
        await logger._AsyncSmartLogger__process_rotate(payload)

    await do_rotation()

    details_text = logger.get_profiling_details()
    assert "Avg steady-state time" in details_text
    assert "Avg spike time" in details_text
    assert "Avg rotation time" in details_text


# ============================================================
# 4. ANSI bleaching edge cases
# ============================================================

@pytest.mark.asyncio
async def test_bleach_non_colored_text_mixed_ansi():
    msg = "plain \x1b[31mRED\x1b[0m more \x1b[32mGREEN\x1b[0m end"
    bleached = AsyncSmartLogger._AsyncSmartLogger__bleach_non_colored_text(msg)
    assert "RED" in bleached
    assert "GREEN" in bleached
    assert "plain" in bleached
    assert "end" in bleached


# ============================================================
# 5. Audit forwarding, prefix, recursion prevention
# ============================================================

@pytest.mark.asyncio
async def test_audit_forwarding_and_prefix(tmp_path):
    log_dir = os.path.abspath(tmp_path.as_posix())

    await AsyncSmartLogger.audit_everything(
        log_dir=log_dir,
        logfile_name="audit.log",
        rotation_logic=None,
        details=None,
    )

    audited_logger = AsyncSmartLogger("audited-src")
    audited_logger.add_console(output_mode="plain")

    await audited_logger.a_info("audited message")
    await audited_logger.flush()

    info = AsyncSmartLogger.audit_handler_info()
    assert info is not None

    audit_path = os.path.join(log_dir, "audit.log")
    text = open(audit_path, "r", encoding="utf-8").read()
    assert "audited-src" in text
    assert "audited message" in text

    await AsyncSmartLogger.terminate_auditing()
    assert AsyncSmartLogger.audit_handler_info() is None


# ============================================================
# 6. stack_info_flag=True, exc_info, merged_kwargs override
# ============================================================

@pytest.mark.asyncio
async def test_stack_info_and_exc_info_and_merged_kwargs(tmp_path):
    logger = AsyncSmartLogger("stack-exc")
    log_dir = os.path.abspath(tmp_path.as_posix())

    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(
            exc_info=True,
            stack_info=True,
        ),
    )

    logger.add_file(log_dir, "stack_exc.log", log_record_details=details)

    try:
        1 / 0
    except ZeroDivisionError:
        await logger.a_error(
            "error happened",
            extra={"foo": "bar"},
            fields={"foo": "baz", "answer": 42},
            exc_info=True,
            stack_info=True,
        )

    await logger.flush()

    text = (tmp_path / "stack_exc.log").read_text(encoding="utf-8")
    assert "error happened" in text
    assert "answer" in text
    assert "baz" in text
    assert "bar" in text
    assert "ZeroDivisionError" in text


# ============================================================
# 7. get_record metadata
# ============================================================

@pytest.mark.asyncio
async def test_get_record_metadata():
    rec = AsyncSmartLogger.get_record(exc_info=True, stack_info=True)
    assert rec.file_name.endswith(".py")
    assert rec.func_name is not None
    assert rec.thread_id is not None
    assert rec.process_id == os.getpid()
    assert rec.stack_info is not None


# ============================================================
# 8. audit handler metadata with rotation_logic
# ============================================================

@pytest.mark.asyncio
async def test_audit_handler_info_with_rotation_logic(tmp_path):
    log_dir = os.path.abspath(tmp_path.as_posix())

    rotation_logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        timestamp=None,
        maxBytes=10,
        backupCount=2,
        expiration_rule=None,
        log_entry_larger_than_maxBytes_behavior=None,
    )

    await AsyncSmartLogger.audit_everything(
        log_dir=log_dir,
        logfile_name="audit_rot.log",
        rotation_logic=rotation_logic,
        details=None,
    )

    info = AsyncSmartLogger.audit_handler_info()
    assert info is not None
    rot = info["rotation"]
    assert rot["maxBytes"] == 10
    assert rot["backupCount"] == 2

    await AsyncSmartLogger.terminate_auditing()
