import logging
from LogSmith.formatter import (
    StructuredColorFormatter,
    LogRecordDetails,
    OptionalRecordFields,
)
from LogSmith.colors import CPrint


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


def test_color_basic():
    fmt = StructuredColorFormatter(LogRecordDetails())
    rec = make_record("hello")
    out = fmt.format(rec)

    assert "hello" in out
    assert "\x1b[" in out  # ANSI present


def test_color_all_fields():
    orf = OptionalRecordFields(logger_name=True)
    details = LogRecordDetails(
        optional_record_fields=orf,
        message_parts_order=["level", "logger_name"],
        color_all_log_record_fields=True,
    )
    fmt = StructuredColorFormatter(details)
    rec = make_record("msg")
    out = fmt.format(rec)

    assert "LOGGER=test" in out
    assert "\x1b[" in out  # colored
