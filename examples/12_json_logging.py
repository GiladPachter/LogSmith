# examples/02_json_logging.py

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

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
