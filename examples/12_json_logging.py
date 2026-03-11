# examples/02_json_logging.py

import logging
from pathlib import Path

from LogSmith import SmartLogger
from LogSmith import LogRecordDetails
from LogSmith import OutputMode  # wherever you placed the enum
from project_definitions import ROOT_DIR


def main():
    levels = SmartLogger.levels()

    # Create logger
    logger = SmartLogger("json_demo", level=levels["DEBUG"])

    # JSON console handler (pretty-printed)
    logger.add_console(
        level=logging.DEBUG,
        log_record_details=LogRecordDetails(),
        output_mode=OutputMode.JSON,
    )

    # NDJSON file handler (compact, one JSON object per line)
    log_dir = str(Path(ROOT_DIR).resolve() / "Logs" / "NDJSON")
    logger.add_file(
        log_dir=log_dir,
        logfile_name="events.ndjson",
        level=logging.DEBUG,
        log_record_details=LogRecordDetails(),
        output_mode=OutputMode.NDJSON,
    )

    logger.info("JSON console + NDJSON file demo started")

    # Structured fields
    logger.info("User login", username="Gilad", action="login")

    # Exception example
    try:
        1 / 0
    except Exception:
        logger.error("An exception occurred", exc_info=True)

    logger.info("Demo complete")


if __name__ == "__main__":
    main()
