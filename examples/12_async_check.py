# examples/11_misc_issues_demo.py

"""
Getting started with asyncSmartLogger
"""

import asyncio
import logging
from LogSmith.smartlogger import SmartLogger
from LogSmith.async_smartlogger import AsyncSmartLogger

async def main():
    SmartLogger.initialize_smartlogger(level=logging.DEBUG)

    logger = AsyncSmartLogger.get("async-demo", logging.DEBUG)
    logger.add_console()

    await logger.info("Hello from async", user="Gilad")
    await logger.error("Something went wrong", code=123)

    await logger.shutdown()

asyncio.run(main())