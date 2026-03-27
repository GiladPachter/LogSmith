import json
import logging
import pytest
from LogSmith.formatter import (
    LogRecordDetails,
    OptionalRecordFields,
    StructuredPlainFormatter,
    StructuredJSONFormatter,
    StructuredNDJSONFormatter,
)


# ------------------------------------------------------------
# Helper: build a LogRecord
# ------------------------------------------------------------
def make_record(msg="hello", level=logging.INFO, **kwargs):
    return logging.LogRecord(
        name="test",
        level=level,
        pathname="x.py",
        lineno=123,
        msg=msg,
        args=(),
        exc_info=kwargs.get("exc_info"),
        func="func",
        sinfo=kwargs.get("stack_info"),
    )


# ------------------------------------------------------------
# 1. Separator must be a single non-alphanumeric, non-bracket char
# ------------------------------------------------------------
def test_invalid_separator():
    with pytest.raises(ValueError):
        LogRecordDetails(separator="ab")

    with pytest.raises(ValueError):
        LogRecordDetails(separator="A")

    with pytest.raises(ValueError):
        LogRecordDetails(separator="(")


# ------------------------------------------------------------
# 2. message_parts_order cannot contain timestamp or message
# ------------------------------------------------------------
def test_invalid_message_parts_order_forbidden_fields():
    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(file_name=True),
            message_parts_order=["timestamp", "file_name", "level"],
        )

    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(file_name=True),
            message_parts_order=["message", "file_name", "level"],
        )


# ------------------------------------------------------------
# 3. message_parts_order must contain level exactly once
# ------------------------------------------------------------
def test_invalid_message_parts_order_missing_level():
    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(file_name=True),
            message_parts_order=["file_name"],
        )


def test_invalid_message_parts_order_duplicate_level():
    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(file_name=True),
            message_parts_order=["level", "file_name", "level"],
        )


# ------------------------------------------------------------
# 4. Optional fields enabled but missing from message_parts_order
# ------------------------------------------------------------
def test_optional_field_enabled_but_missing():
    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(file_name=True, lineno=True),
            message_parts_order=["file_name", "level"],  # lineno missing
        )


# ------------------------------------------------------------
# 5. Optional field disabled but appears in message_parts_order
# ------------------------------------------------------------
def test_optional_field_disabled_but_present():
    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(file_name=False),
            message_parts_order=["file_name", "level"],
        )


# ------------------------------------------------------------
# 6. Diagnostics-only mode (exc_info or stack_info only)
# ------------------------------------------------------------
def test_diagnostics_only_mode():
    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(exc_info=True),
        message_parts_order=None,
    )
    fmt = StructuredPlainFormatter(details)

    try:
        raise RuntimeError("boom")
    except Exception as e:
        rec = make_record("err", exc_info=(type(e), e, e.__traceback__))

    out = fmt.format(rec)
    assert "RuntimeError" in out


# ------------------------------------------------------------
# 7. Invalid: diagnostics enabled but inline fields disabled AND message_parts_order provided
# ------------------------------------------------------------
def test_invalid_diagnostics_with_order():
    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(exc_info=True),
            message_parts_order=["exc_info"],
        )


# ------------------------------------------------------------
# 8. Fractional timestamp formatting (%1f ... %6f)
# ------------------------------------------------------------
def test_fractional_timestamp_formatting():
    details = LogRecordDetails(datefmt="%Y-%m-%d %H:%M:%S.%3f")
    fmt = StructuredPlainFormatter(details)

    rec = make_record("hello")
    out = fmt.format(rec)

    # Must contain exactly 3 fractional digits
    assert "." in out
    frac = out.split(" ")[1].split(".")[1][:3]
    assert len(frac) == 3


# ------------------------------------------------------------
# 9. Extras merging edge case: fields override extras
# ------------------------------------------------------------
def test_extras_merging_priority():
    details = LogRecordDetails()
    fmt = StructuredPlainFormatter(details)

    rec = make_record("hello")
    rec.__dict__["extra"] = {"user": "gilad"}
    rec.__dict__["fields"] = {"user": "override", "x": 5}

    out = fmt.format(rec)

    assert "override" in out
    assert "x=5" in out
    assert "gilad" in out


# ------------------------------------------------------------
# 10. ANSI stripping edge case
# ------------------------------------------------------------
def test_ansi_stripping_edge_case():
    details = LogRecordDetails()
    fmt = StructuredPlainFormatter(details)

    msg = "\x1b[31mRED\x1b[0m"
    rec = make_record(msg)

    out = fmt.format(rec)

    # Formatter does NOT strip ANSI — SmartLogger does.
    assert "\x1b[31m" in out
    assert "RED" in out


# ------------------------------------------------------------
# 11. JSON optional-field filtering edge case
# ------------------------------------------------------------
def test_json_optional_field_filtering():
    details = LogRecordDetails(
        # optional_record_fields=OptionalRecordFields(file_name=False, lineno=False),
        # message_parts_order = ["file_name", "lineno", "level"]
    )
    fmt = StructuredJSONFormatter(details)

    rec = make_record("hello")
    data = json.loads(fmt.format(rec))

    assert "file_name" not in data
    assert "lineno" not in data


# ------------------------------------------------------------
# 12. NDJSON ordering edge case
# ------------------------------------------------------------
def test_ndjson_ordering():
    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(file_name=True, lineno=True),
        message_parts_order=["file_name", "lineno", "level"],
    )
    fmt = StructuredNDJSONFormatter(details)

    rec = make_record("hello")
    data = json.loads(fmt.format(rec))

    keys = list(data.keys())
    assert keys.index("file_name") < keys.index("lineno") < keys.index("level")
