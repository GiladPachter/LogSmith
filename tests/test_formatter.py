import json
import logging
import pytest
import sys
import LogSmith.formatter as F

from LogSmith.formatter import (
    StructuredPlainFormatter,
    StructuredJSONFormatter,
    StructuredNDJSONFormatter,
    LogRecordDetails,
    OptionalRecordFields,
)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def make_record(**kwargs):
    defaults = dict(
        name="test",
        level=logging.INFO,
        pathname="x.py",
        lineno=10,
        msg="hello",
        args=(),
        exc_info=None,
        func="f",
        sinfo=None,
    )
    defaults.update(kwargs)
    return logging.LogRecord(**defaults)


# ------------------------------------------------------------
# 1. SIMPLE MODE (rf=None)
# ------------------------------------------------------------

def test_plain_simple_mode_extras_comma_join():
    details = LogRecordDetails(optional_record_fields=None)
    fmt = StructuredPlainFormatter(details)

    rec = make_record()
    rec.__dict__["foo"] = 1
    rec.__dict__["bar"] = 2

    out = fmt.format(rec)
    assert "{foo=1, bar=2}" in out


# ------------------------------------------------------------
# 2. STRICT MODE — inline ordering
# ------------------------------------------------------------

def test_plain_strict_mode_ordering():
    orf = OptionalRecordFields(
        logger_name=True,
        file_name=True,
        lineno=True,
    )
    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=["logger_name", "level", "file_name", "lineno"],
    )
    fmt = StructuredPlainFormatter(details)

    rec = make_record()
    out = fmt.format(rec)

    assert "LOGGER=test" in out
    assert "INFO" in out
    assert "x.py" in out
    assert "L=10" in out


# ------------------------------------------------------------
# 3. STRICT MODE — diagnostics-only mode
# ------------------------------------------------------------

def test_plain_strict_mode_diagnostics_only():
    orf = OptionalRecordFields(exc_info=True)
    details = LogRecordDetails(optional_record_fields=orf)

    fmt = StructuredPlainFormatter(details)

    try:
        raise ValueError("boom")
    except ValueError:
        rec = make_record(exc_info=sys.exc_info())

    out = fmt.format(rec)
    assert "ValueError" in out
    assert "boom" in out


# ------------------------------------------------------------
# 4. _extract_extras edge cases
# ------------------------------------------------------------

def test_extract_extras_fields_merge():
    rec = make_record()
    rec.__dict__["fields"] = {"a": 1, "b": 2}
    rec.__dict__["x"] = 99

    extras = F._extract_extras(rec)
    assert extras == {"a": 1, "b": 2, "x": 99}


def test_extract_extras_no_fields():
    rec = make_record()
    rec.__dict__["foo"] = 123
    extras = F._extract_extras(rec)
    assert extras == {"foo": 123}


# ------------------------------------------------------------
# 5. Timestamp fractional formatting
# ------------------------------------------------------------

def test_timestamp_fractional_seconds():
    details = LogRecordDetails(datefmt="%Y-%m-%d %H:%M:%S.%4f")
    fmt = StructuredPlainFormatter(details)

    rec = make_record()
    out = fmt.format(rec)

    frac = out.split(".")[-1][:4]
    assert len(frac) == 4
    assert frac.isdigit()


def test_timestamp_invalid_fractional_directive():
    details = LogRecordDetails(datefmt="%Y-%m-%d %H:%M:%S.%9f")
    fmt = StructuredPlainFormatter(details)

    rec = make_record()
    with pytest.raises(ValueError):
        fmt.format(rec)


# ------------------------------------------------------------
# 6. JSON formatter — optional field filtering
# ------------------------------------------------------------

def test_json_optional_field_filtering():
    # Must enable at least one inline field
    orf = OptionalRecordFields(
        logger_name=True,
        file_name=False,
        lineno=False,
        func_name=False,
        thread_id=False,
        thread_name=False,
        process_id=False,
        process_name=False,
    )
    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=["logger_name", "level"],
    )
    fmt = StructuredJSONFormatter(details)

    rec = make_record()
    data = json.loads(fmt.format(rec))

    # logger_name should remain
    assert "logger" in data

    # disabled fields must be removed
    assert "file_name" not in data
    assert "lineno" not in data
    assert "func_name" not in data


# ------------------------------------------------------------
# 7. JSON formatter — ordering
# ------------------------------------------------------------

def test_json_ordering():
    orf = OptionalRecordFields(logger_name=True, file_name=True)
    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=["logger_name", "file_name", "level"],
    )
    fmt = StructuredJSONFormatter(details)

    rec = make_record()
    data = json.loads(fmt.format(rec))

    keys = list(data.keys())

    # timestamp always first
    assert keys[0] == "timestamp"

    # named_args always last
    assert keys[-1] == "named_args"

    # message must appear before named_args but after metadata
    assert "message" in keys
    assert keys.index("message") < keys.index("named_args")


# ------------------------------------------------------------
# 8. NDJSON formatter
# ------------------------------------------------------------

def test_ndjson_basic():
    details = LogRecordDetails(optional_record_fields=None)
    fmt = StructuredNDJSONFormatter(details)

    rec = make_record()
    data = json.loads(fmt.format(rec))

    assert data["message"] == "hello"
    assert data["level"] == "INFO"


# ------------------------------------------------------------
# 9. Plain formatter — fallback diagnostics
# ------------------------------------------------------------

def test_plain_fallback_stack_info():
    # Enable one inline field so strict mode is active
    orf = OptionalRecordFields(
        logger_name=True,
        stack_info=True,
    )
    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=["logger_name", "level"],  # stack_info NOT included
    )

    fmt = StructuredPlainFormatter(details)

    rec = make_record()
    rec.stack_info = "STACK!"   # <-- THIS is the missing piece

    out = fmt.format(rec)

    # Fallback stack_info should appear on a new line
    assert "STACK!" in out


# ------------------------------------------------------------
# 10. JSON formatter — exception + stack info
# ------------------------------------------------------------

def test_json_exception_and_stack():
    orf = OptionalRecordFields(
        logger_name=True,
        stack_info=True,
    )
    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=["logger_name", "level"],
    )
    fmt = StructuredJSONFormatter(details)

    try:
        raise RuntimeError("oops")
    except RuntimeError:
        rec = make_record(exc_info=sys.exc_info())
        rec.stack_info = "STACK"

    data = json.loads(fmt.format(rec))

    assert "exception" in data
    assert "stack_info" in data
