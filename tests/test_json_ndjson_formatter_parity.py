import json
import logging

from LogSmith.formatter import (
    StructuredJSONFormatter,
    StructuredNDJSONFormatter,
    LogRecordDetails,
    OptionalRecordFields,
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
# 1. Basic JSON formatting
# ------------------------------------------------------------
def test_basic_json_formatting():
    details = LogRecordDetails()
    fmt = StructuredJSONFormatter(details, indent=None)

    rec = make_record("hello")
    out = fmt.format(rec)

    data = json.loads(out)
    assert data["message"] == "hello"
    assert data["level"] == "INFO"


# ------------------------------------------------------------
# 2. NDJSON produces one JSON object per line
# ------------------------------------------------------------
def test_ndjson_single_line():
    details = LogRecordDetails()
    fmt = StructuredNDJSONFormatter(details)

    rec = make_record("hello")
    out = fmt.format(rec)

    assert "\n" not in out
    data = json.loads(out)
    assert data["message"] == "hello"


# ------------------------------------------------------------
# 3. ANSI is stripped
# ------------------------------------------------------------
def test_json_strips_ansi():
    details = LogRecordDetails()
    fmt = StructuredJSONFormatter(details)

    colored = "\x1b[31mRED\x1b[0m"
    rec = make_record(colored)

    out = fmt.format(rec)
    data = json.loads(out)

    assert data["message"] == "RED"
    assert "\x1b" not in data["message"]


# ------------------------------------------------------------
# 4. OptionalRecordFields filtering
# ------------------------------------------------------------
def test_optional_fields_filtering():
    details = LogRecordDetails(
        # optional_record_fields=OptionalRecordFields(
        #     file_name=True,
        #     lineno=True,
        #     thread_id=True,
        # ),
        # message_parts_order=[
        #     "file_name",
        #     "lineno",
        #     "thread_id",
        #     "level",
        # ]
    )
    fmt = StructuredJSONFormatter(details)

    rec = make_record("hello")
    out = fmt.format(rec)
    data = json.loads(out)

    assert "file_name" not in data
    assert "lineno" not in data
    assert "thread_id" not in data
    assert data["message"] == "hello"


# ------------------------------------------------------------
# 5. message_parts_order reordering
# ------------------------------------------------------------
def test_message_parts_order():
    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(file_name=True, lineno=True),
        message_parts_order=["file_name", "lineno", "level"],
    )
    fmt = StructuredJSONFormatter(details)

    rec = make_record("hello")
    out = fmt.format(rec)
    data = json.loads(out)

    # JSON ordering is preserved in Python 3.7+
    keys = list(data.keys())

    assert keys.index("file_name") < keys.index("lineno") < keys.index("level")


# ------------------------------------------------------------
# 6. extras merged into named_args
# ------------------------------------------------------------
def test_extras_in_named_args():
    details = LogRecordDetails()
    fmt = StructuredJSONFormatter(details)

    rec = make_record("hello")
    rec.__dict__["fields"] = {"user": "gilad", "x": 5}

    out = fmt.format(rec)
    data = json.loads(out)

    assert data["named_args"]["user"] == "gilad"
    assert data["named_args"]["x"] == 5


# ------------------------------------------------------------
# 7. exc_info serialization
# ------------------------------------------------------------
def test_exc_info_serialization():
    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(exc_info=True),
        # message_parts_order=["level", "exc_info"],
    )
    fmt = StructuredJSONFormatter(details)

    try:
        raise RuntimeError("boom")
    except Exception as e:
        rec = make_record("err", exc_info=(type(e), e, e.__traceback__))

    out = fmt.format(rec)
    data = json.loads(out)

    assert "exception" in data
    assert data["exception"]["type"] == "RuntimeError"
    assert "boom" in data["exception"]["message"]


# ------------------------------------------------------------
# 8. stack_info serialization
# ------------------------------------------------------------
def test_stack_info_serialization():
    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(stack_info=True),
        # message_parts_order=["level", "stack_info"],
    )
    fmt = StructuredJSONFormatter(details)

    rec = make_record("msg", stack_info="STACKINFO")
    out = fmt.format(rec)
    data = json.loads(out)

    assert "stack_info" in data
    assert "STACKINFO" in data["stack_info"][0]


# ------------------------------------------------------------
# 9. JSON vs NDJSON parity (same dict)
# ------------------------------------------------------------
def test_json_ndjson_parity():
    details = LogRecordDetails()
    rec = make_record("hello", level=logging.WARNING)

    fmt_json = StructuredJSONFormatter(details)
    fmt_nd = StructuredNDJSONFormatter(details)

    d1 = json.loads(fmt_json.format(rec))
    d2 = json.loads(fmt_nd.format(rec))

    assert d1 == d2
