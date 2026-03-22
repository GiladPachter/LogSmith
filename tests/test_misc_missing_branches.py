import logging

from LogSmith import AsyncSmartLogger, SmartLogger, CPrint


async def test_async_smartlogger_no_parent():
    logger = AsyncSmartLogger("app.UI")
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
