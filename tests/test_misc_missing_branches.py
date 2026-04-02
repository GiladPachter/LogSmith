import logging

import pytest

from LogSmith import AsyncSmartLogger, SmartLogger, CPrint, OutputMode, LevelStyle, NEON_THEME, PASTEL_THEME, \
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
    a_logger.destroy()


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

    logger.remove_file_handler(logger.name + ".log", str(tmp_path))

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
    AsyncSmartLogger.apply_color_theme(PASTEL_THEME)

    info_meta = LEVELS.get("INFO")
    assert info_meta["style"].fg == PASTEL_THEME[20].fg
