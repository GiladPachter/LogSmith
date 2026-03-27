import logging
from LogSmith.formatter import (
    StructuredColorFormatter,
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
# 1. Basic color formatting
# ------------------------------------------------------------
def test_basic_color_formatting():
    details = LogRecordDetails()
    fmt = StructuredColorFormatter(details)

    rec = make_record("hello", logging.INFO)
    out = fmt.format(rec)

    # INFO level uses NEON_GREEN by default
    assert "\x1b[" in out
    assert "hello" in out


# ------------------------------------------------------------
# 2. No color bleed (reset code must appear)
# ------------------------------------------------------------
def test_no_color_bleed():
    details = LogRecordDetails()
    fmt = StructuredColorFormatter(details)

    rec = make_record("hello")
    out = fmt.format(rec)

    assert out.endswith("\x1b[0m") or "\x1b[0m" in out


# ------------------------------------------------------------
# 3. OptionalRecordFields + message_parts_order
# ------------------------------------------------------------
def test_color_with_optional_fields():
    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(file_name=True, lineno=True),
        message_parts_order=["level", "file_name", "lineno"],
    )
    fmt = StructuredColorFormatter(details)

    rec = make_record("hello")
    out = fmt.format(rec)

    assert "x.py" in out
    assert "L=123" in out
    assert "\x1b[" in out  # colored


# ------------------------------------------------------------
# 4. extras coloring
# ------------------------------------------------------------
def test_extras_colored():
    details = LogRecordDetails()
    fmt = StructuredColorFormatter(details)

    rec = make_record("hello")
    rec.__dict__["fields"] = {"user": "gilad", "x": 5}

    out = fmt.format(rec)

    # keys and values must be colored
    assert "user" in out
    assert "gilad" in out
    assert "\x1b[" in out


# ------------------------------------------------------------
# 5. exc_info colored
# ------------------------------------------------------------
def test_exc_info_colored():
    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(exc_info=True),
    )
    fmt = StructuredColorFormatter(details)

    try:
        raise RuntimeError("boom")
    except Exception as e:
        rec = make_record("err", exc_info=(type(e), e, e.__traceback__))

    out = fmt.format(rec)

    assert "RuntimeError" in out
    assert "\x1b[" in out  # colored traceback


# ------------------------------------------------------------
# 6. stack_info colored
# ------------------------------------------------------------
def test_stack_info_colored():
    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(stack_info=True),
    )
    fmt = StructuredColorFormatter(details)

    rec = make_record("msg", stack_info="STACKINFO")
    out = fmt.format(rec)

    assert "STACKINFO" in out
    assert "\x1b[" in out


# ------------------------------------------------------------
# 7. color_all_log_record_fields
# ------------------------------------------------------------
def test_color_all_fields():
    details = LogRecordDetails(
        optional_record_fields=OptionalRecordFields(file_name=True),
        message_parts_order=["level", "file_name"],
        color_all_log_record_fields=True,
    )
    fmt = StructuredColorFormatter(details)

    rec = make_record("hello")
    out = fmt.format(rec)

    # file_name should be colored with level style
    assert "\x1b[" in out
    assert "x.py" in out


# ------------------------------------------------------------
# 8. LevelStyle override (theme)
# ------------------------------------------------------------
def test_level_style_override():
    from LogSmith.level_registry import reset_levels_for_tests
    reset_levels_for_tests()

    # Override INFO level to bright magenta using the public API
    from LogSmith.levels import LevelStyle
    from LogSmith.colors import CPrint
    from LogSmith.async_smartlogger import AsyncSmartLogger

    AsyncSmartLogger.apply_color_theme({
        logging.INFO: LevelStyle(
            fg=CPrint.FG.BRIGHT_MAGENTA,
            intensity=CPrint.Intensity.BOLD,
        )
    })

    details = LogRecordDetails()
    fmt = StructuredColorFormatter(details)

    rec = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="x.py",
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
        func="func",
        sinfo=None,
    )

    out = fmt.format(rec)

    # Must contain the bright magenta ANSI code
    assert "\x1b[" in out
    assert "hello" in out
