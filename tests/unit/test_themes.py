import pytest

from io import StringIO

from LogSmith import SmartLogger
from LogSmith import AsyncSmartLogger
from LogSmith import NEON_THEME


def test_smartlogger_reset_to_default_theme():
    levels = SmartLogger.levels()
    logger = SmartLogger("theme_reset_smart", levels["TRACE"])

    # No console handler yet
    assert logger.console_handler is None

    # Add console handler
    logger.add_console()
    assert logger.console_handler is not None

    # Retrieve the actual handler (the one inside Python logging)
    handler = logger._SmartLogger__py_logger.handlers[0]

    # Patch stream
    buf = StringIO()
    handler.stream = buf

    # Apply NEON theme
    SmartLogger.apply_color_theme(NEON_THEME)

    logger.trace("neon trace")
    handler.flush()
    neon_output = buf.getvalue()
    buf.truncate(0)
    buf.seek(0)

    # Reset to default theme
    SmartLogger.apply_color_theme(None)

    logger.trace("default trace")
    handler.flush()
    default_output = buf.getvalue()

    # Assertions
    assert neon_output != default_output
    assert "default trace" in default_output

    logger.destroy()


@pytest.mark.asyncio
async def test_asyncsmartlogger_reset_to_default_theme():
    levels = AsyncSmartLogger.levels()
    logger = AsyncSmartLogger("theme_reset_async", levels["TRACE"])

    # No console handler yet
    assert logger.console_handler is None

    # Add console handler
    logger.add_console()
    assert logger.console_handler is not None

    # Retrieve actual handler
    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    # Patch stream
    buf = StringIO()
    handler.stream = buf

    # Apply NEON theme
    await AsyncSmartLogger.apply_color_theme(NEON_THEME)

    await logger.a_trace("neon trace")
    await logger.flush()
    neon_output = buf.getvalue()
    buf.truncate(0)
    buf.seek(0)

    # Reset to default theme
    await AsyncSmartLogger.apply_color_theme(None)

    await logger.a_trace("default trace")
    await logger.flush()
    default_output = buf.getvalue()

    # Assertions
    assert neon_output != default_output
    assert "default trace" in default_output

    await logger.shutdown()
    logger.destroy()
