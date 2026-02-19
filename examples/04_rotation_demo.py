# examples/04_rotation_demo.py

"""
Demonstrates SmartLogger rotation logic:
- Size-based rotation
- Time-based rotation
- Combined rotation (size + time)
- Comments explaining daily/weekly behavior
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
from LogSmith import RotationLogic, When
from LogSmith import LogRecordDetails, OptionalRecordFields

from project_definitions import ROOT_DIR


# ----------------------------------------------------------------------------------------------------------
# 1. Initialization — MUST be done at application entry point
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()
SmartLogger.initialize_smartlogger(level=levels["TRACE"])

print("\nRotation demo\n=============")
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 2. Prepare log directory and clean old files
# ----------------------------------------------------------------------------------------------------------
print("\nPreparing log directory...")

log_dir = Path(ROOT_DIR) / "Logs" / "examples" / "rotation_demo"

# Delete all rotation-related files from previous runs
if log_dir.exists():
    for f in log_dir.iterdir():
        if f.is_file():
            f.unlink()

print("Old rotation files removed.")


# ----------------------------------------------------------------------------------------------------------
# 3. Create logger
# ----------------------------------------------------------------------------------------------------------
print("\nCreating logger 'rotation_demo'...")
time.sleep(0.1)

logger = SmartLogger.get("rotation_demo", level=levels["TRACE"])
logger.add_console(level=levels["TRACE"])


# ----------------------------------------------------------------------------------------------------------
# 4. Common formatting for all file handlers
# ----------------------------------------------------------------------------------------------------------
details = LogRecordDetails(
    datefmt="%Y-%m-%d %H:%M:%S",
    separator="|",
    optional_record_fields=OptionalRecordFields(
        process_id=True,
        thread_id=True,
    ),
    message_parts_order=[
        "process_id",
        "thread_id",
        "level",
    ],
)


# ==========================================================================================================
# SIZE-BASED ROTATION
# ==========================================================================================================
print("\nSize-based rotation (maxBytes=2000)...")
time.sleep(0.1)

logger.add_file(
    log_dir=str(log_dir),
    logfile_name="size_based.log",
    level=levels["TRACE"],
    rotation_logic=RotationLogic(
        maxBytes=2000,     # rotate when file exceeds ~2 KB
        backupCount=5,
    ),
    log_record_details=details,
)

for i in range(40):
    logger.info(f"[size] message {i}")
    time.sleep(0.02)

time.sleep(0.1)
print("Size-based rotation complete.")
time.sleep(0.1)


# ==========================================================================================================
# TIME-BASED ROTATION
# ==========================================================================================================
print("\nTime-based rotation (rotate every second)...")
time.sleep(0.1)

logger.add_file(
    log_dir=str(log_dir),
    logfile_name="time_based.log",
    level=levels["TRACE"],
    rotation_logic=RotationLogic(
        when=When.SECOND,   # rotate every second
        interval=1,
        backupCount=5,
    ),
    log_record_details=details,
)

# Write for ~3 seconds to trigger multiple rotations
start = time.time()
while time.time() - start < 3:
    logger.debug("[time] rotating...")
    time.sleep(0.1)

time.sleep(0.1)
print("Time-based rotation complete.")
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# NOTE ABOUT DAILY/WEEKLY ROTATION
# ----------------------------------------------------------------------------------------------------------
print("\nDaily/Weekly rotation behavior:")
time.sleep(0.1)

print(
    "- When=When.DAY rotates at midnight local time.\n"
    "- When=When.WEEK rotates at the start of the week (Monday).\n"
    "- interval=N means 'every N days' or 'every N weeks'.\n"
    "- These rotations occur even if the file is small.\n"
)
time.sleep(0.1)


# ==========================================================================================================
# COMBINED ROTATION (size + time)
# ==========================================================================================================
print("\nCombined rotation (maxBytes + time)...")
time.sleep(0.1)

logger.add_file(
    log_dir=str(log_dir),
    logfile_name="combined.log",
    level=levels["TRACE"],
    rotation_logic=RotationLogic(
        maxBytes=1500,
        when=When.SECOND,
        interval=1,
        backupCount=5,
    ),
    log_record_details=details,
)

start = time.time()
while time.time() - start < 2:
    logger.warning("[combined] rotating...")
    time.sleep(0.05)

time.sleep(0.1)
print("Combined rotation complete.")
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 5. Show handler_info (JSON-safe)
# ----------------------------------------------------------------------------------------------------------
print("\nHandler info:\n-------------")
time.sleep(0.1)

print(logger.handler_info_json)
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 6. SmartLogger rotation safeguards
# ----------------------------------------------------------------------------------------------------------
print("\nSmartLogger rotation safeguards:\n--------------------------------")
time.sleep(0.1)

print(
    "- Validates rotation parameters\n"
    "- Prevents invalid combinations (e.g., negative sizes)\n"
    "- Ensures backupCount is respected\n"
    "- Ensures time-based rotation triggers reliably\n"
    "- Ensures size-based rotation triggers immediately when threshold is exceeded\n"
)
time.sleep(0.1)

print("\nRotation demo complete.\n")
