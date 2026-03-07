import pytest

from LogSmith import SmartLogger, AsyncSmartLogger, LevelStyle, CPrint


def test_levels_contains_core_levels():
    levels = SmartLogger.levels()
    for name in ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        assert name in levels
        assert isinstance(levels[name], int)


def test_register_dynamic_level_creates_method_and_value_unique():
    levels_before = SmartLogger.levels()
    assert "NOTICE" not in levels_before

    SmartLogger.register_level(name="NOTICE", value=25)
    levels_after = SmartLogger.levels()

    assert "NOTICE" in levels_after
    assert levels_after["NOTICE"] == 25

    logger = SmartLogger("dynamic.level.test", level=levels_after["TRACE"])
    logger.add_console()

    # dynamic method should exist
    assert hasattr(logger, "notice")

    # calling it should not raise
    logger.notice("dynamic level works")


def test_register_dynamic_level_with_style_and_theme_integration():
    SmartLogger.register_level(
        name="SECURITY",
        value=45,
        style=LevelStyle(fg=CPrint.FG.BRIGHT_RED, intensity=CPrint.Intensity.BOLD),
    )

    levels = SmartLogger.levels()
    assert "SECURITY" in levels

    logger = SmartLogger("security.logger", level=levels["TRACE"])
    logger.add_console()

    # method exists
    assert hasattr(logger, "security")
    logger.security("security event", user="gilad")


@pytest.mark.asyncio
async def test_async_dynamic_level_registration_and_method():
    AsyncSmartLogger.register_level("SUCCESS", 35)
    levels = AsyncSmartLogger.levels()
    assert "SUCCESS" in levels

    logger = AsyncSmartLogger("async.dynamic", level=levels["TRACE"])
    logger.add_console()

    assert hasattr(logger, "a_success")
    await logger.a_success("async success")
    await logger.flush()
