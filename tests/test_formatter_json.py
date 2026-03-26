import logging
import json
import sys

from LogSmith.formatter import (
    StructuredJSONFormatter,
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
# JSON BASIC
# ------------------------------------------------------------
def test_json_basic():
    fmt = StructuredJSONFormatter(LogRecordDetails())
    rec = make_record("hello")
    out = fmt.format(rec)
    data = json.loads(out)

    assert data["message"] == "hello"
    assert data["level"] == "INFO"
    assert "timestamp" in data


# ------------------------------------------------------------
# JSON optional field filtering
# ------------------------------------------------------------
def test_json_optional_field_filtering():
    fmt = StructuredJSONFormatter(LogRecordDetails())

    rec = make_record("x")
    data = json.loads(fmt.format(rec))

    assert "logger" not in data
    assert "file_name" not in data
    assert "file_path" not in data


# ------------------------------------------------------------
# JSON exception formatting
# ------------------------------------------------------------
def test_json_exception():
    fmt = StructuredJSONFormatter(LogRecordDetails())

    # noinspection PyBroadException
    try:
        raise RuntimeError("boom")
    except Exception:
        rec = make_record("x", exc_info=sys.exc_info())

    data = json.loads(fmt.format(rec))

    assert "exception" in data
    assert data["exception"]["type"] == "RuntimeError"
    assert "boom" in data["exception"]["message"]
