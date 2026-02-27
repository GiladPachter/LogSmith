# examples/12_async_json_logging.py

import asyncio
import logging
from pathlib import Path

from LogSmith import AsyncSmartLogger, a_stdout
from LogSmith import LogRecordDetails
from LogSmith import OutputMode


async def main():
    await a_stdout("\nAsync JSON / NDJSON logging demo\n")

    logger = AsyncSmartLogger("async_json_demo", level=logging.DEBUG)

    # JSON console (pretty)
    logger.add_console(
        level=logging.DEBUG,
        log_record_details=LogRecordDetails(),
        output_mode=OutputMode.JSON,
    )

    # NDJSON file
    log_dir = str(Path(__file__).resolve().parent / "logs")
    logger.add_file(
        log_dir=log_dir,
        logfile_name="async_events.ndjson",
        level=logging.DEBUG,
        log_record_details=LogRecordDetails(),
        output_mode=OutputMode.NDJSON,
    )

    await logger.a_info("Async JSON/NDJSON demo started")

    # Structured fields
    await logger.a_info("User login", username="Gilad", action="login")

    # Exception example
    try:
        {}["missing"]
    except Exception:
        await logger.a_error("Async exception occurred", exc_info=True)

    await logger.a_info("Async demo complete")

    await logger.flush()


if __name__ == "__main__":
    asyncio.run(main())