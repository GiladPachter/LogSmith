import os.path
import sys

import pytest
import logging
# noinspection PyProtectedMember
from LogSmith.formatter import _format_timestamp
from LogSmith.formatter import LogRecordDetails, OptionalRecordFields
from LogSmith.formatter import StructuredPlainFormatter
from LogSmith.formatter import StructuredColorFormatter
from LogSmith.formatter import StructuredJSONFormatter
from LogSmith.formatter import StructuredNDJSONFormatter


def make_record(msg="x"):
    return logging.LogRecord(
        name="t",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )

def test_timestamp_fractional_digits():
    rec = make_record()
    for digits in range(1, 7):
        fmt = f"%Y-%m-%d %H:%M:%S.%{digits}f"
        ts = _format_timestamp(rec, fmt)
        assert len(ts.split(".")[1]) == digits


def test_timestamp_invalid_fractional():
    rec = make_record()
    with pytest.raises(ValueError):
        _format_timestamp(rec, "%Y-%m-%d %H:%M:%S.%0f")


def test_timestamp_plain_f():
    rec = make_record()
    ts = _format_timestamp(rec, "%Y-%m-%d %H:%M:%S.%f")
    assert "." in ts


def test_timestamp_none_datefmt():
    rec = make_record()
    ts = _format_timestamp(rec, None)
    assert " " in ts


def test_optional_fields_missing_message_parts_order():
    orf = OptionalRecordFields(file_name=True)
    with pytest.raises(ValueError):
        LogRecordDetails(optional_record_fields=orf)


def test_optional_fields_forbidden_timestamp():
    orf = OptionalRecordFields(file_name=True)
    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=orf,
            message_parts_order=["timestamp", "file_name", "level"]
        )


def test_optional_fields_missing_inline_field():
    orf = OptionalRecordFields(file_name=True, lineno=True)
    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=orf,
            message_parts_order=["file_name", "level"]
        )


def test_plain_formatter_strict_mode():
    orf = OptionalRecordFields(file_name=True, lineno=True)
    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=["file_name", "lineno", "level"]
    )
    fmt = StructuredPlainFormatter(details)
    rec = make_record("hello")
    out = fmt.format(rec)
    assert "hello" in out
    assert "L=" in out
    assert os.path.basename(__file__) in out


def test_color_formatter_all_fields():
    orf = OptionalRecordFields(
        file_name=True,
        lineno=True,
        func_name=True,
        thread_id=True,
        process_id=True,
    )
    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=[
            "file_name",
            "lineno",
            "func_name",
            "thread_id",
            "process_id",
            "level"
        ]
    )
    fmt = StructuredColorFormatter(details)
    rec = make_record("colored")
    out = fmt.format(rec)
    assert "colored" in out
    assert os.path.basename(__file__) in out
    assert "L=" in out


def test_json_formatter_optional_filtering():
    # orf = OptionalRecordFields(file_name=False, lineno=False)
    # details = LogRecordDetails(optional_record_fields=orf)
    # fmt = StructuredJSONFormatter(details)
    fmt = StructuredJSONFormatter(details = LogRecordDetails())
    rec = make_record("json")
    out = fmt.format(rec)
    assert '"message": "json"' in out
    assert "file_name" not in out
    assert "lineno" not in out

def test_json_formatter_exception_and_stack():
    rec = make_record("boom")
    # noinspection PyBroadException
    try:
        raise ValueError("x")
    except Exception:
        rec.exc_info = sys.exc_info()
    fmt = StructuredJSONFormatter(LogRecordDetails())
    out = fmt.format(rec)
    assert "exception" in out


def test_ndjson_formatter():
    fmt = StructuredNDJSONFormatter(LogRecordDetails())
    rec = make_record("nd")
    out = fmt.format(rec)
    assert out.startswith("{") and out.endswith("}")


