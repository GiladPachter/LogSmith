# examples/03_file_output_demo.py

"""
Demonstrates LogSmith file output:
- add_file()
- rotation basics
- color-preserving file output
- reading ANSI-colored content back from file
- handler_info (JSON-safe)
- LogSmith's path validation safeguards
"""

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import time
from pathlib import Path

from LogSmith import SmartLogger, stdout
from LogSmith import LogRecordDetails, OptionalRecordFields
from LogSmith import RotationLogic, When
from LogSmith import CPrint

from project_definitions import ROOT_DIR

# ----------------------------------------------------------------------------------------------------------
# 1. Initialization
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()

stdout("\nFile output demo\n================")

# ----------------------------------------------------------------------------------------------------------
# 2. Create logger
# ----------------------------------------------------------------------------------------------------------
stdout("\nCreating logger 'file_demo'...")

logger = SmartLogger("file_demo", level=levels["TRACE"])
logger.add_console(level=levels["TRACE"])   # console for visibility

# ----------------------------------------------------------------------------------------------------------
# 3. Prepare log directory and clean old files
# ----------------------------------------------------------------------------------------------------------
stdout("\nPreparing log directory...")

log_dir = Path(ROOT_DIR) / "Logs" / "examples" / "file_demo"
log_dir.mkdir(parents=True, exist_ok=True)

files_to_delete = [
    "plain_output.log",
    "rotating.log",
    "color_preserved.log",
]

# Delete rotating.log.* as well
for f in log_dir.iterdir():
    if f.name.startswith("rotating.log"):
        f.unlink()

for fname in files_to_delete:
    f = log_dir / fname
    if f.exists():
        f.unlink()

stdout("Old demo files removed.")

# ----------------------------------------------------------------------------------------------------------
# 4. File handler with basic formatting
# ----------------------------------------------------------------------------------------------------------
stdout("\nAdding file handler (plain formatting)...")

file_details = LogRecordDetails(
    datefmt="%Y-%m-%d %H:%M:%S",
    separator="|",
    optional_record_fields=OptionalRecordFields(
        process_id=True,
        thread_id=True,
        exc_info=True,
        stack_info=True,
    ),
    message_parts_order=[
        "process_id",
        "thread_id",
        "level",
    ],
)

logger.add_file(
    log_dir=str(log_dir),
    logfile_name="plain_output.log",
    level=levels["TRACE"],
    log_record_details=file_details,
)

logger.info("This message goes to both console and file.")

# ----------------------------------------------------------------------------------------------------------
# 5. Demonstrate rotation basics
# ----------------------------------------------------------------------------------------------------------
stdout("\nAdding rotating file handler...")

rotation = RotationLogic(
    when=When.SECOND,   # rotate every second
    interval=1,
    maxBytes=5000,      # or size-based rollover
    backupCount=5,
)

logger.add_file(
    log_dir=str(log_dir),
    logfile_name="rotating.log",
    level=levels["TRACE"],
    rotation_logic=rotation,
)

stdout(logger.handler_info_json)

logger.info("Rotation handler attached.")

for i in range(20):
    logger.debug(f"Rotating message {i}")

# ----------------------------------------------------------------------------------------------------------
# 6. Demonstrate color-preserving file output
# ----------------------------------------------------------------------------------------------------------
stdout("\nAdding color-preserving file handler...")

color_file = log_dir / "color_preserved.log"

logger.add_file(
    log_dir=str(log_dir),
    logfile_name="color_preserved.log",
    level=levels["TRACE"],
    log_record_details=file_details,
    do_not_sanitize_colors_from_string=True,
)

stdout("\nWriting colored text via logger.raw():")
colored = CPrint.colorize("This text contains ANSI colors", fg=CPrint.FG.BRIGHT_MAGENTA)
logger.raw(colored)

stdout("\nEscaped version of colored text (for inspection):")
stdout(CPrint.escape_ansi_for_display(colored))

# ----------------------------------------------------------------------------------------------------------
# 7. Read the color-preserved file back
# ----------------------------------------------------------------------------------------------------------
stdout("\nReading color-preserved text back from file:")

with open(color_file, "r", encoding="utf-8") as fh:
    file_content = fh.read().rstrip()

stdout("---------------------------------------------")
stdout(file_content)
stdout("---------------------------------------------")

stdout("\nEscaped file content:")
stdout(CPrint.escape_ansi_for_display(file_content))

# ----------------------------------------------------------------------------------------------------------
# 8. Show handler_info (JSON-safe)
# ----------------------------------------------------------------------------------------------------------
stdout("\nHandlers details:\n-----------------")
stdout(logger.handler_info_json)

# ----------------------------------------------------------------------------------------------------------
# 9. SmartLogger safeguards (contextually relevant here)
# ----------------------------------------------------------------------------------------------------------
stdout("\nSmartLogger file-output safeguards:"
      "\n-----------------------------------\n"
      "- log_dir must be an absolute, normalized path (prevents accidental use of relative paths)\n"
      "- log_dir created if not exists\n"
      "- prevents multiple handlers writing to the same file\n"
      "- protects against invalid rotation configurations\n"
      "\n\n"
      "File output demo complete."
)
