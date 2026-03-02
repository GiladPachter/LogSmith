from pathlib import Path
from LogSmith import SmartLogger, OutputMode, LogRecordDetails, OptionalRecordFields
from project_definitions import ROOT_DIR

logger = SmartLogger("json_demo", level=10)

logger.add_console(output_mode=OutputMode.JSON)
logger.add_file(
    log_dir = str(Path(ROOT_DIR).resolve() / "logs" / "NDJSON"),    # enforces normalized path
    logfile_name="events.ndjson",
    output_mode=OutputMode.NDJSON,
)

logger.info("Hello NDJSON")