import pytest
import sys

from io import StringIO

from LogSmith import SmartLogger
from LogSmith import AsyncSmartLogger


def test_smartlogger_stdout_without_console_handler():
    logger = SmartLogger("stdout_no_console")

    assert logger.console_handler is None

    buf = StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf

    logger.stdout("hello no console")

    sys.stdout = old_stdout
    output = buf.getvalue().strip()

    assert output == "hello no console"

    logger.destroy()


def test_smartlogger_stdout_with_console_handler():
    logger = SmartLogger("stdout_with_console")
    logger.add_console()

    assert logger.console_handler is not None

    # Get the actual handler
    handler = logger._SmartLogger__py_logger.handlers[0]

    buf = StringIO()
    handler.stream = buf

    logger.stdout("hello console")
    handler.flush()

    output = buf.getvalue()

    # Must NOT equal raw text — because formatting is applied
    assert output != "hello console"

    # But the message must appear inside the formatted output
    assert "hello console" in output

    logger.destroy()




@pytest.mark.asyncio
async def test_asyncsmartlogger_a_stdout_without_console_handler():
    logger = AsyncSmartLogger("a_stdout_no_console")

    assert logger.console_handler is None

    buf = StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf

    await logger.a_stdout("hello no console")

    sys.stdout = old_stdout
    output = buf.getvalue().strip()

    assert output == "hello no console"

    await logger.shutdown()
    logger.destroy()


@pytest.mark.asyncio
async def test_asyncsmartlogger_a_stdout_with_console_handler():
    logger = AsyncSmartLogger("a_stdout_with_console")
    logger.add_console()

    assert logger.console_handler is not None

    handler = logger._AsyncSmartLogger__py_logger.handlers[0]

    buf = StringIO()
    handler.stream = buf

    await logger.a_stdout("hello console")
    await logger.flush()

    output = buf.getvalue()

    # Must NOT equal raw text — formatting applied
    assert output != "hello console"

    # But message must appear inside formatted output
    assert "hello console" in output

    await logger.shutdown()
    logger.destroy()
