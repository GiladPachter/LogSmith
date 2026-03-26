import pytest
import logging
from LogSmith.formatter import (
    LogRecordDetails,
    OptionalRecordFields,
    StructuredPlainFormatter,
)


# ------------------------------------------------------------
# 1. SIMPLE MODE (optional_record_fields=None)
# ------------------------------------------------------------
def test_simple_mode_basic():
    details = LogRecordDetails()
    fmt = StructuredPlainFormatter(details)

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="x.py",
        lineno=10,
        msg="hello",
        args=(),
        exc_info=None,
    )

    out = fmt.format(record)
    assert "hello" in out
    assert "INFO" in out
    assert "x.py" not in out  # simple mode excludes optional fields


# ------------------------------------------------------------
# 2. STRICT MODE: valid configuration
# ------------------------------------------------------------
def test_strict_mode_valid():
    orf = OptionalRecordFields(
        file_name=True,
        lineno=True,
    )

    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=["level", "file_name", "lineno"],
    )

    fmt = StructuredPlainFormatter(details)

    record = logging.LogRecord(
        name="test",
        level=logging.WARNING,
        pathname="/tmp/x.py",
        lineno=42,
        msg="msg",
        args=(),
        exc_info=None,
    )

    out = fmt.format(record)
    assert "x.py" in out
    assert "L=42" in out
    assert "WARNING" in out


# ------------------------------------------------------------
# 3. STRICT MODE: missing message_parts_order
# ------------------------------------------------------------
def test_strict_mode_missing_mpo():
    orf = OptionalRecordFields(file_name=True)

    with pytest.raises(ValueError):
        LogRecordDetails(optional_record_fields=orf)


# ------------------------------------------------------------
# 4. STRICT MODE: forbidden fields in message_parts_order
# ------------------------------------------------------------
def test_strict_mode_forbidden_fields():
    orf = OptionalRecordFields(file_name=True)

    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=orf,
            message_parts_order=["timestamp", "file_name"],
        )


# ------------------------------------------------------------
# 5. STRICT MODE: level must appear exactly once
# ------------------------------------------------------------
def test_strict_mode_level_missing():
    orf = OptionalRecordFields(file_name=True)

    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=orf,
            message_parts_order=["file_name"],
        )


def test_strict_mode_level_twice():
    orf = OptionalRecordFields(file_name=True)

    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=orf,
            message_parts_order=["level", "file_name", "level"],
        )


# ------------------------------------------------------------
# 6. STRICT MODE: optional field enabled but missing in MPO
# ------------------------------------------------------------
def test_strict_mode_missing_enabled_field():
    orf = OptionalRecordFields(file_name=True, lineno=True)

    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=orf,
            message_parts_order=["level", "file_name"],
        )


# ------------------------------------------------------------
# 7. STRICT MODE: optional field disabled but present in MPO
# ------------------------------------------------------------
def test_strict_mode_disabled_field_present():
    orf = OptionalRecordFields(file_name=False)

    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=orf,
            message_parts_order=["level", "file_name"],
        )


# ------------------------------------------------------------
# 8. STRICT MODE: diagnostics-only mode (exc_info=True)
# ------------------------------------------------------------
def test_strict_mode_diagnostics_only():
    orf = OptionalRecordFields(exc_info=True)

    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=None,  # allowed in diagnostics-only mode
    )

    fmt = StructuredPlainFormatter(details)

    try:
        raise RuntimeError("boom")
    except Exception as e:
        import sys
        exc_info = (type(e), e, e.__traceback__)

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="x.py",
            lineno=1,
            msg="msg",
            args=(),
            exc_info=exc_info,   # <-- REAL exc_info tuple
        )

    out = fmt.format(record)
    assert "RuntimeError" in out
    assert "boom" in out


# ------------------------------------------------------------
# 9. STRICT MODE: invalid message part
# ------------------------------------------------------------
def test_strict_mode_invalid_message_part():
    orf = OptionalRecordFields(file_name=True)

    with pytest.raises(ValueError):
        LogRecordDetails(
            optional_record_fields=orf,
            message_parts_order=["level", "file_name", "not_a_field"],
        )


# ------------------------------------------------------------
# 10. STRICT MODE: stack_info enabled
# ------------------------------------------------------------
def test_strict_mode_exc_info_diagnostics_only():
    orf = OptionalRecordFields(exc_info=True)

    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=None,
    )

    fmt = StructuredPlainFormatter(details)

    try:
        raise RuntimeError("boom")
    except Exception as e:
        import sys
        exc_info = (type(e), e, e.__traceback__)

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="x.py",
            lineno=1,
            msg="msg",
            args=(),
            exc_info=exc_info,
        )

    out = fmt.format(record)
    assert "RuntimeError" in out
    assert "boom" in out


def test_strict_mode_stack_info_ignored():
    orf = OptionalRecordFields(
        file_name=True,
        stack_info=True,
    )

    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=["level", "file_name"],
    )

    fmt = StructuredPlainFormatter(details)

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="x.py",
        lineno=1,
        msg="msg",
        args=(),
        exc_info=None,
        stack_info="STACK",
    )

    out = fmt.format(record)

    # stack_info is ignored in strict mode
    assert "STACK" not in out
    assert "INFO" in out
    assert "x.py" in out
    assert "msg" in out


def test_diagnostics_only_stack_info_ignored():
    orf = OptionalRecordFields(stack_info=True)

    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=None,
    )

    fmt = StructuredPlainFormatter(details)

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="x.py",
        lineno=1,
        msg="msg",
        args=(),
        exc_info=None,
        stack_info="STACK",
    )

    out = fmt.format(record)

    # stack_info is ignored even in diagnostics-only mode
    assert "STACK" not in out


def test_diagnostics_only_exc_info_printed():
    orf = OptionalRecordFields(exc_info=True)

    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=None,
    )

    fmt = StructuredPlainFormatter(details)

    try:
        raise RuntimeError("boom")
    except Exception as e:
        exc_info = (type(e), e, e.__traceback__)
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="x.py",
            lineno=1,
            msg="msg",
            args=(),
            exc_info=exc_info,
        )

    out = fmt.format(record)

    assert "RuntimeError" in out
    assert "boom" in out
