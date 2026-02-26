# examples/11_misc_issues_demo.py

"""
Getting started with asyncSmartLogger
"""

import asyncio
import logging

from LogSmith import CPrint
from LogSmith.smartlogger import SmartLogger
from LogSmith.async_smartlogger import AsyncSmartLogger

async def main():
    # SmartLogger.initialize_smartlogger(level=logging.DEBUG)

    logger = AsyncSmartLogger.get("async-demo", logging.DEBUG)
    logger.add_console()

    await logger.a_info("Hello from a_sync", user="Gilad")
    await logger.a_error("Something a_sync went wrong", code=123)

    colored = [
        CPrint.colorize("RAW", fg=CPrint.FG.BRIGHT_RED),
        CPrint.colorize("text", fg=CPrint.FG.ORANGE),
        CPrint.colorize("rocks", fg=CPrint.FG.BRIGHT_YELLOW),
        CPrint.colorize("in", fg=CPrint.FG.BRIGHT_GREEN),
        CPrint.colorize("multiple", fg=CPrint.FG.BRIGHT_BLUE),
        CPrint.colorize("colors", fg=CPrint.FG.SOFT_PURPLE)
    ]
    await logger.a_raw("a_raw: " + " ".join(colored))

    await logger.flush()
    await logger.shutdown()

asyncio.run(main())