# examples/03_file_output_demo.py

"""
Demonstrates SmartLogger file output:
- add_file()
- rotation basics
- color-preserving file output
- reading ANSI-colored content back from file
- handler_info (JSON-safe)
- SmartLogger's path validation safeguards
"""

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import time
import json
import os

from LogSmith import SmartLogger
from LogSmith import LogRecordDetails, OptionalRecordFields
from LogSmith import RotationLogic, When
from LogSmith import CPrint

from project_definitions import ROOT_DIR


# ----------------------------------------------------------------------------------------------------------
# 1. Initialization — MUST be done at application entry point
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()
SmartLogger.initialize_smartlogger(level=levels["TRACE"])

print("\nFile output demo\n================")
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 2. Create logger
# ----------------------------------------------------------------------------------------------------------
print("\nCreating logger 'file_demo'...")
time.sleep(0.1)

logger = SmartLogger.get("file_demo", level=levels["TRACE"])
logger.add_console(level=levels["TRACE"])   # console for visibility


# ----------------------------------------------------------------------------------------------------------
# 3. Prepare log directory and clean old files
# ----------------------------------------------------------------------------------------------------------
print("\nPreparing log directory...")
time.sleep(0.1)

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

print("Old demo files removed.")
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 4. File handler with basic formatting
# ----------------------------------------------------------------------------------------------------------
print("\nAdding file handler (plain formatting)...")

time.sleep(0.1)

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
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 5. Demonstrate rotation basics
# ----------------------------------------------------------------------------------------------------------
print("\nAdding rotating file handler...")
time.sleep(0.1)

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

print(logger.handler_info_json)

logger.info("Rotation handler attached.")
time.sleep(0.1)

for i in range(20):
    logger.debug(f"Rotating message {i}")
    time.sleep(0.05)


# ----------------------------------------------------------------------------------------------------------
# 6. Demonstrate color-preserving file output
# ----------------------------------------------------------------------------------------------------------
print("\nAdding color-preserving file handler...")
time.sleep(0.1)

color_file = log_dir / "color_preserved.log"

logger.add_file(
    log_dir=str(log_dir),
    logfile_name="color_preserved.log",
    level=levels["TRACE"],
    log_record_details=file_details,
    do_not_sanitize_colors_from_string=True,
)

colored = CPrint.colorize("This text contains ANSI colors", fg=CPrint.FG.BRIGHT_MAGENTA)

print("\nWriting colored text via logger.raw():")
time.sleep(0.1)
logger.raw(colored)
time.sleep(0.1)

print("\nEscaped version (for inspection):")
time.sleep(0.1)
print(CPrint.escape_ansi_for_display(colored))
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 7. Read the color-preserved file back
# ----------------------------------------------------------------------------------------------------------
print("\nReading color-preserved file back...")
time.sleep(0.1)

with open(color_file, "r", encoding="utf-8") as fh:
    file_content = fh.read().rstrip()

print("\nRaw file content:")
time.sleep(0.1)
print(file_content)
time.sleep(0.1)

print("\nEscaped file content:")
time.sleep(0.1)
print(CPrint.escape_ansi_for_display(file_content))
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 8. Show handler_info (JSON-safe)
# ----------------------------------------------------------------------------------------------------------
print("\nHandler info:\n-------------")
time.sleep(0.1)

print(logger.handler_info_json)
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 9. SmartLogger safeguards (contextually relevant here)
# ----------------------------------------------------------------------------------------------------------
print("\nSmartLogger file-output safeguards:\n-----------------------------------")
time.sleep(0.1)

print(
    "- log_dir must be an absolute, normalized path (prevents accidental use of relative paths)\n"
    "- log_dir created if not exists\n"
    "- prevents multiple handlers writing to the same file\n"
    "- protects against invalid rotation configurations\n"
)

time.sleep(0.1)
print("\nFile output demo complete.\n")
