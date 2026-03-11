# examples/12_async_json_logging.py

import asyncio
import logging
from pathlib import Path

from LogSmith import AsyncSmartLogger, a_stdout
from LogSmith import LogRecordDetails
from LogSmith import OutputMode
from project_definitions import ROOT_DIR


async def main():
    await a_stdout("\nAsync JSON / NDJSON logging demo\n")

    levels = AsyncSmartLogger.levels()

    logger = AsyncSmartLogger("async_json_demo", level=levels["DEBUG"])

    # JSON console (pretty)
    logger.add_console(
        level=logging.DEBUG,
        log_record_details=LogRecordDetails(),
        output_mode=OutputMode.JSON,
    )

    # NDJSON file
    log_dir = str(Path(ROOT_DIR).resolve() / "Logs" / "NDJSON")
    logger.add_file(
        log_dir=log_dir,
        logfile_name="async_events.ndjson",
        level=logging.DEBUG,
        log_record_details=LogRecordDetails(),
        output_mode=OutputMode.NDJSON,
    )

    await logger.a_info("Async JSON / NDJSON demo started")

    # Structured fields
    await logger.a_info("User login", username="Gilad", action="login")

    # Exception example
    # noinspection PyBroadException
    try:
        {}["missing"]
    except Exception:
        await logger.a_error("Async exception occurred", exc_info=True)

    await logger.a_info("Async demo complete")

    await logger.flush()


if __name__ == "__main__":
    asyncio.run(main())