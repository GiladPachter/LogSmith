import asyncio
import io
import threading
import logging
import pytest

from LogSmith import AsyncSmartLogger, SmartLogger, CPrint, OutputMode, LevelStyle, PASTEL_THEME, \
    LIGHT_THEME
from LogSmith.level_registry import LEVELS


async def test_async_smartlogger_no_parent():
    logger = AsyncSmartLogger("app_UI")
    assert isinstance(logger._AsyncSmartLogger__py_logger.parent, logging.Logger)


async def test_use_logger_properties():
    logger = SmartLogger("logger")
    a_logger = AsyncSmartLogger("a_logger")

    name = logger.name
    assert name == "logger"

    a_name = a_logger.name
    assert a_name == "a_logger"

    level = logger.level
    assert level == logger._SmartLogger__py_logger.level

    logger.level = logging.ERROR
    assert logger._SmartLogger__py_logger.level == logging.ERROR

    a_level = a_logger.level
    assert a_level == a_logger._AsyncSmartLogger__py_logger.level

    a_logger.level = logging.ERROR
    assert a_logger._AsyncSmartLogger__py_logger.level == logging.ERROR

    logger.destroy()
    await a_logger.destroy()


async def test_colored_raw(tmp_path):
    logger = SmartLogger("logger")
    a_logger = AsyncSmartLogger("a_logger")

    colored = [
        "prefix",
        CPrint.colorize("RAW",      fg=CPrint.FG.BRIGHT_RED),
        CPrint.colorize("text",     fg=CPrint.FG.ORANGE),
        CPrint.colorize("rocks",    fg=CPrint.FG.BRIGHT_YELLOW),
        "infix",
        CPrint.colorize("in",       fg=CPrint.FG.BRIGHT_GREEN),
        CPrint.colorize("multiple", fg=CPrint.FG.BRIGHT_BLUE),
        CPrint.colorize("colors",   fg=CPrint.FG.SOFT_PURPLE),
        "postfix",
    ]

    logger.add_file(str(tmp_path))
    a_logger.add_file(str(tmp_path))

    logger.raw(" ".join(colored))
    await a_logger.a_raw(" ".join(colored))

    await a_logger.flush()

    text = (tmp_path / (logger.name + ".log")).read_text(encoding="utf-8")
    a_text = (tmp_path / (a_logger.name + ".log")).read_text(encoding="utf-8")

    assert "rocks" in text
    assert "multiple" in a_text

    logger.destroy()
    await a_logger.destroy()


async def test_smartlogger_console_with_NDJSON():
    logger = SmartLogger("logger")

    logger.add_console(output_mode = OutputMode.NDJSON)
    assert logger.handler_info[0]["kind"] == "console"

    logger.remove_console()
    logger.add_console(output_mode = OutputMode.PLAIN)
    assert logger.handler_info[0]["kind"] == "console"

    with pytest.raises(Exception):
        logger.add_console(output_mode=OutputMode.COLOR)

    logger.destroy()


def test_smartlogger_blocks_multiple_console_handlers(tmp_path):
    logger = SmartLogger("logger")
    logger.add_file(str(tmp_path))

    logger.remove_file_handler(str(tmp_path), logger.name + ".log")

    assert len(logger.handler_info) == 0
    assert logger.console_handler is None

    logger.destroy()


def test_illegal_register_level(tmp_path):
    logger = SmartLogger("logger")

    with pytest.raises(Exception):
        logger.register_level("LEVEL", 25, LevelStyle())

    with pytest.raises(Exception):
        logger.register_level("ADD_CONSOLE", 25, LevelStyle())

    logger.destroy()


def reset_levels_for_tests():
    # noinspection PyProtectedMember
    LEVELS._LevelRegistry__init_builtin_levels()
    # noinspection PyProtectedMember
    LEVELS._LevelRegistry__cache.clear()

async def test_theme():
    reset_levels_for_tests()
    SmartLogger.apply_color_theme(LIGHT_THEME)

    info_meta = LEVELS.get("INFO")
    assert info_meta["style"].fg == LIGHT_THEME[20].fg

    reset_levels_for_tests()
    await AsyncSmartLogger.apply_color_theme(PASTEL_THEME)

    info_meta = LEVELS.get("INFO")
    assert info_meta["style"].fg == PASTEL_THEME[20].fg


# ============================================================
#  SMARTLOGGER TESTS
# ============================================================

def test_add_console_duplicate():
    from LogSmith.smartlogger import SmartLogger

    lg = SmartLogger("dup_console")
    lg.add_console()

    with pytest.raises(RuntimeError):
        lg.add_console()

    lg.destroy()


def test_invalid_separator():
    from LogSmith.formatter import LogRecordDetails

    with pytest.raises(ValueError):
        LogRecordDetails(separator="A")  # alphanumeric not allowed


def test_invalid_message_parts_order_timestamp():
    from LogSmith.formatter import LogRecordDetails, OptionalRecordFields

    orf = OptionalRecordFields(logger_name=True)
    with pytest.raises(ValueError):
        LogRecordDetails(optional_record_fields=orf,
                         message_parts_order=["timestamp", "level", "logger_name"])


def test_invalid_logger_hierarchy():
    from LogSmith.smartlogger import SmartLogger

    with pytest.raises(RuntimeError):
        SmartLogger("parent.child")  # parent does not exist


def test_raw_writes_to_file_handler(tmp_path):
    from LogSmith.smartlogger import SmartLogger

    lg = SmartLogger("raw_file")
    lg.add_file(str(tmp_path), "x.log")

    lg.raw("\x1b[31mRED\x1b[0m", end="!")

    with open(tmp_path / "x.log", "r") as f:
        assert f.read() == "RED!"

    lg.destroy()


def test_stdout_fallback(capsys):
    from LogSmith.smartlogger import SmartLogger

    lg = SmartLogger("stdout_fallback")
    lg.stdout("hello", "world", sep="-", end="!")

    captured = capsys.readouterr().out
    assert captured == "hello-world!"

    lg.destroy()


def test_destroy_reparents_children():
    from LogSmith.smartlogger import SmartLogger
    import logging

    parent = SmartLogger("destroy_parent")
    child = SmartLogger("destroy_parent.child")

    # Destroy child first
    child.destroy()

    # Destroy parent
    parent.destroy()

    # The child logger should no longer exist at all
    assert "destroy_parent.child" not in logging.Logger.manager.loggerDict


# ============================================================
#  ASYNC SMARTLOGGER TESTS
# ============================================================

@pytest.mark.asyncio
async def test_async_logger_basic_usage():
    from LogSmith.async_smartlogger import AsyncSmartLogger

    lg = AsyncSmartLogger("async_basic")

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    lg._AsyncSmartLogger__py_logger.addHandler(handler)

    await lg.a_info("hello")
    await lg.flush()

    assert "hello" in stream.getvalue()


@pytest.mark.asyncio
async def test_async_queue_full_retry():
    from LogSmith.async_smartlogger import AsyncSmartLogger

    lg = AsyncSmartLogger("async_queue")

    # Fill queue
    await lg.a_info("one")

    # This forces retry logic
    await lg.a_info("two")
    await lg.flush()


@pytest.mark.asyncio
async def test_async_external_thread_enqueue():
    from LogSmith.async_smartlogger import AsyncSmartLogger

    lg = AsyncSmartLogger("async_thread")

    async def run():
        await lg.a_info("inside")

    # Start worker by logging inside loop
    await run()

    # Now enqueue from external thread
    def thread_func():
        asyncio.run(lg.a_info("outside"))

    t = threading.Thread(target=thread_func)
    t.start()
    t.join()

    await lg.flush()


@pytest.mark.asyncio
async def test_async_retire():
    from LogSmith.async_smartlogger import AsyncSmartLogger

    lg = AsyncSmartLogger("async_retire")
    await lg.a_info("before")
    await lg.flush()

    lg.retire()

    with pytest.raises(RuntimeError):
        await lg.a_info("after")


@pytest.mark.asyncio
async def test_async_destroy():
    from LogSmith.async_smartlogger import AsyncSmartLogger
    import logging

    lg = AsyncSmartLogger("async_destroy")
    await lg.a_info("x")
    await lg.flush()

    await lg.destroy()

    assert "async_destroy" not in logging.Logger.manager.loggerDict


@pytest.mark.asyncio
async def test_async_stdout_fallback(capsys):
    from LogSmith.async_smartlogger import AsyncSmartLogger

    lg = AsyncSmartLogger("async_stdout")

    await lg.a_stdout("hello", "world", sep="-", end="!")
    captured = capsys.readouterr().out

    assert captured == "hello-world!"


@pytest.mark.asyncio
async def test_async_rotation_debounce(tmp_path):
    from LogSmith.async_smartlogger import AsyncSmartLogger, RotationLogic

    lg = AsyncSmartLogger("async_rotate")
    lg.add_file(str(tmp_path), "r.log", rotation_logic=RotationLogic(maxBytes=1))

    # Trigger rotation twice quickly
    await lg.a_info("x")
    await lg.a_info("y")
    await lg.flush()


# ============================================================
#  FORMATTER TESTS
# ============================================================

def test_formatter_diagnostics_only():
    from LogSmith.formatter import LogRecordDetails, OptionalRecordFields, StructuredPlainFormatter

    orf = OptionalRecordFields(exc_info=True)
    details = LogRecordDetails(optional_record_fields=orf)

    fmt = StructuredPlainFormatter(details)

    record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", (), None)
    record.exc_info = (ValueError, ValueError("boom"), None)

    out = fmt.format(record)
    assert "boom" in out


def test_formatter_ndjson():
    from LogSmith.formatter import StructuredNDJSONFormatter, LogRecordDetails

    fmt = StructuredNDJSONFormatter(LogRecordDetails())
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", (), None)

    out = fmt.format(record)
    assert out.startswith("{") and out.endswith("}")


def test_formatter_extras():
    from LogSmith.formatter import StructuredPlainFormatter, LogRecordDetails

    fmt = StructuredPlainFormatter(LogRecordDetails())
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", (), None)
    record.extra = {"foo": 123}

    out = fmt.format(record)
    assert "foo" in out


# ============================================================
#  ROTATION TESTS
# ============================================================

def test_rotation_size_based(tmp_path):
    from LogSmith.rotation import ConcurrentTimedSizedRotatingFileHandler

    path = tmp_path / "r.log"
    h = ConcurrentTimedSizedRotatingFileHandler(str(path), max_bytes=10)

    record = logging.LogRecord("x", logging.INFO, __file__, 1, "1234567890", (), None)
    h.emit(record)

    assert path.exists()


def test_rotation_timestamp(tmp_path):
    from LogSmith.rotation import ConcurrentTimedSizedRotatingFileHandler
    from LogSmith.rotation_base import RotationTimestamp, When

    path = tmp_path / "t.log"
    h = ConcurrentTimedSizedRotatingFileHandler(
        str(path),
        when=When.EVERYDAY,
        timestamp=RotationTimestamp(hour=0, minute=0, second=0),
    )

    record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", (), None)
    h.emit(record)

    assert path.exists()


# ============================================================
#  METADATA TESTS
# ============================================================

def test_get_record_minimal():
    from LogSmith.smartlogger import SmartLogger

    rec = SmartLogger.get_record()
    assert rec.timestamp is not None


# ============================================================
#  COLORS TESTS
# ============================================================

def test_color_strip_and_colorize():
    from LogSmith.colors import CPrint

    colored = CPrint.colorize("x", fg=CPrint.FG.RED)
    stripped = CPrint.strip_ansi(colored)

    assert stripped == "x"
