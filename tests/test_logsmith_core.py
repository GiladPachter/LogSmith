# test_logsmith_core.py

import asyncio
import logging
import os
from pathlib import Path

import pytest

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.formatter import (
    LogRecordDetails,
    OptionalRecordFields,
    StructuredPlainFormatter,
    StructuredJSONFormatter,
)
from LogSmith.rotation_base import RotationTimestamp, RotationLogic
from LogSmith.smartlogger import SmartLogger
from LogSmith.colors import CPrint


# =========================
# rotation_base.py
# =========================

def test_rotationtimestamp_to_seconds():
    ts = RotationTimestamp(hour=1, minute=2, second=3)
    assert ts.to_seconds() == 1 * 3600 + 2 * 60 + 3


def test_rotationlogic_validation_negative_interval():
    with pytest.raises(ValueError):
        RotationLogic(interval=-1)


def test_rotationlogic_validation_negative_maxbytes():
    with pytest.raises(ValueError):
        RotationLogic(maxBytes=-10)


def test_rotationlogic_validation_negative_backupcount():
    with pytest.raises(ValueError):
        RotationLogic(backupCount=-1)


# =========================
# formatter.py – LogRecordDetails & StructuredPlainFormatter
# =========================

def test_logrecorddetails_simple_mode_valid():
    d = LogRecordDetails()
    assert d.separator == "•"
    assert d.optional_record_fields is None


def test_logrecorddetails_invalid_separator():
    with pytest.raises(ValueError):
        LogRecordDetails(separator="ab")


def test_logrecorddetails_strict_mode_requires_message_parts():
    orf = OptionalRecordFields(logger_name=True)
    with pytest.raises(ValueError):
        LogRecordDetails(optional_record_fields=orf, message_parts_order=None)


def test_logrecorddetails_strict_mode_valid():
    orf = OptionalRecordFields(logger_name=True)
    d = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=["level", "logger_name"],
    )
    assert d.optional_record_fields.logger_name
    assert d.message_parts_order == ["level", "logger_name"]


def _make_record(level=logging.INFO, msg="hello", **extras):
    logger = logging.getLogger("test_logger_for_formatter")
    record = logger.makeRecord(
        name=logger.name,
        level=level,
        fn=__file__,
        lno=123,
        msg=msg,
        args=(),
        exc_info=None,
    )
    for k, v in extras.items():
        setattr(record, k, v)
    return record


def test_structured_plain_formatter_simple_mode_includes_extras():
    d = LogRecordDetails()
    fmt = StructuredPlainFormatter(d)
    rec = _make_record(msg="hi", user="gilad", fields={"x": 1})
    line = fmt.format(rec)
    assert "hi" in line
    assert "user='gilad'" in line
    assert "x=1" in line


def test_structured_plain_formatter_strict_mode_order():
    orf = OptionalRecordFields(logger_name=True, lineno=True)
    d = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=["logger_name", "level", "lineno"],
    )
    fmt = StructuredPlainFormatter(d)
    rec = _make_record(msg="msg")
    line = fmt.format(rec)
    # timestamp • LOGGER=... • LEVEL • L=...
    parts = [p.strip() for p in line.split(d.separator)]
    assert "LOGGER=" in parts[1]
    assert "L=" in parts[3]
    assert "msg" in parts[-1]


# =========================
# formatter.py – StructuredJSONFormatter
# =========================

def test_structured_json_formatter_respects_optional_fields():
    orf = OptionalRecordFields(
        logger_name=True,
    )
    details = LogRecordDetails(optional_record_fields=orf,
                               message_parts_order=["level",
                                                    "logger_name",
                                                    ])
    fmt = StructuredJSONFormatter(details, indent=None)

    rec = _make_record(msg="json-test")
    text = fmt.format(rec)
    import json as _json
    data = _json.loads(text)

    assert data["message"] == "json-test"
    assert "logger" in data
    assert "file_name" not in data
    assert "file_path" not in data


# =========================
# smartlogger.py – console & file handlers, raw
# =========================

def test_smartlogger_add_console_once():
    logger = SmartLogger("smartlogger_console_test")
    logger.add_console()
    assert logger.console_handler is not None
    with pytest.raises(RuntimeError):
        logger.add_console()


def test_smartlogger_add_file_uses_normalized_dir(tmp_path):
    logger = SmartLogger("smartlogger_file_test")
    log_dir = str(tmp_path)
    logger.add_file(log_dir=log_dir, logfile_name="app.log")
    files = logger.file_handlers
    assert len(files) == 1
    assert Path(files[0]["path"]).name == "app.log"


def test_smartlogger_add_file_rejects_non_normalized(tmp_path):
    logger = SmartLogger("smartlogger_file_norm_test")
    # introduce a trailing slash difference
    log_dir = str(tmp_path)
    non_normalized = log_dir + os.sep + "."
    with pytest.raises(ValueError):
        logger.add_file(log_dir=non_normalized, logfile_name="x.log")


def test_smartlogger_raw_sanitizes_file_and_colors_console(tmp_path, capsys):
    logger = SmartLogger("smartlogger_raw_test")
    # console
    logger.add_console()
    # file
    logger.add_file(log_dir=str(tmp_path), logfile_name="raw.log")

    colored = CPrint.colorize("hello", fg=CPrint.FG.BRIGHT_RED)
    logger.raw(logging.INFO, colored, end="")

    # console output should still contain ANSI
    captured = capsys.readouterr()
    assert "\x1b[" in captured.out

    # file should be stripped of ANSI
    log_file = tmp_path / "raw.log"
    content = log_file.read_text(encoding="utf-8")
    assert "hello" in content
    assert "\x1b[" not in content


# =========================
# async_smartlogger.py – basic behavior
# =========================

@pytest.mark.asyncio
async def test_asyncsmartlogger_add_console_deduplicates():
    logger = AsyncSmartLogger("async_console_test")
    logger.add_console()
    # second call should be a no-op, not an error
    logger.add_console()
    assert logger.console_handler is not None
    assert logger.console_handler["kind"] == "console"


@pytest.mark.asyncio
async def test_asyncsmartlogger_add_file_and_log_to_file(tmp_path):
    logger = AsyncSmartLogger("async_file_test")
    log_dir = str(tmp_path)
    logger.add_file(log_dir=log_dir, logfile_name="async.log")

    await logger.a_info("hello async")

    # give worker a moment to flush
    await asyncio.sleep(0.1)

    log_file = tmp_path / "async.log"
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "hello async" in content


@pytest.mark.asyncio
async def test_asyncsmartlogger_add_file_requires_normalized(tmp_path):
    logger = AsyncSmartLogger("async_file_norm_test")
    log_dir = str(tmp_path)
    non_normalized = log_dir + os.sep + "."
    with pytest.raises(ValueError):
        logger.add_file(log_dir=non_normalized, logfile_name="x.log")


@pytest.mark.asyncio
async def test_asyncsmartlogger_raw_respects_sanitization(tmp_path):
    logger = AsyncSmartLogger("async_raw_test")
    logger.add_file(
        log_dir=str(tmp_path),
        logfile_name="raw_async.log",
        preserve_colors_in_log_files=False,
    )

    colored = CPrint.colorize("async-raw", fg=CPrint.FG.BRIGHT_GREEN)
    await logger.a_raw(logging.INFO, colored, end="")

    await asyncio.sleep(0.1)

    content = (tmp_path / "raw_async.log").read_text(encoding="utf-8")
    assert "async-raw" in content
    assert "\x1b[" not in content
