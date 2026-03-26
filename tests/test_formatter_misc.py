import logging
from LogSmith.formatter import PassthroughFormatter, AuditFormatter, LogRecordDetails


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


def test_passthrough_formatter_preserves_ansi():
    fmt = PassthroughFormatter()
    rec = make_record("\x1b[31mRED\x1b[0m")
    out = fmt.format(rec)
    assert "\x1b[31m" in out


def test_audit_formatter_prefix():
    details = LogRecordDetails()
    fmt = AuditFormatter(details)

    rec = make_record("hello")
    out = fmt.format(rec)

    assert out.startswith("[test]: ")
    assert "hello" in out
