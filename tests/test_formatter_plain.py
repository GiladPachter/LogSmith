import logging
import sys

import pytest
from LogSmith.formatter import (
    StructuredPlainFormatter,
    LogRecordDetails,
    OptionalRecordFields,
)


def make_record(msg="hello", level=logging.INFO, **kwargs):
    return logging.LogRecord(
        name="test",
        level=level,
        pathname=__file__,
        lineno=10,
        msg=msg,
        args=(),
        exc_info=kwargs.get("exc_info"),
        func="func",
        sinfo=kwargs.get("stack_info"),
    )


# ------------------------------------------------------------
# SIMPLE MODE
# ------------------------------------------------------------
def test_plain_simple_mode_basic():
    fmt = StructuredPlainFormatter(LogRecordDetails())
    rec = make_record("hello")
    out = fmt.format(rec)
    assert "hello" in out
    assert rec.levelname in out


# ------------------------------------------------------------
# STRICT MODE: inline fields
# ------------------------------------------------------------
def test_plain_strict_mode_all_fields():
    orf = OptionalRecordFields(
        relative_created=True,
        logger_name=True,
        file_path=True,
        file_name=True,
        lineno=True,
        func_name=True,
        thread_id=True,
        thread_name=True,
        process_id=True,
        process_name=True,
    )
    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=[
            "level",
            "relative_created",
            "logger_name",
            "file_path",
            "file_name",
            "lineno",
            "func_name",
            "thread_id",
            "thread_name",
            "process_id",
            "process_name",
        ],
    )
    fmt = StructuredPlainFormatter(details)
    rec = make_record("msg")
    out = fmt.format(rec)

    assert "msg" in out
    assert "LOGGER=test" in out
    assert "L=10" in out
    assert rec.levelname in out


# ------------------------------------------------------------
# STRICT MODE: diagnostics-only
# ------------------------------------------------------------
def test_plain_strict_mode_diagnostics_only():
    orf = OptionalRecordFields(exc_info=True)
    details = LogRecordDetails(optional_record_fields=orf)
    fmt = StructuredPlainFormatter(details)

    try:
        raise ValueError("boom")
    except Exception:
        rec = make_record("x", exc_info=sys.exc_info())

    out = fmt.format(rec)
    assert "ValueError" in out
    assert "boom" in out


# ------------------------------------------------------------
# INVALID CONFIGURATIONS
# ------------------------------------------------------------
def test_plain_invalid_message_parts_order_missing_level():
    orf = OptionalRecordFields(logger_name=True)
    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=orf,
            message_parts_order=["logger_name"],
        )


def test_plain_invalid_message_parts_order_forbidden_fields():
    orf = OptionalRecordFields(logger_name=True)
    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=orf,
            message_parts_order=["timestamp", "logger_name", "level"],
        )


def test_plain_invalid_optional_field_mismatch():
    orf = OptionalRecordFields(logger_name=False)
    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=orf,
            message_parts_order=["level", "logger_name"],
        )
