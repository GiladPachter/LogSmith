# examples/04_rotation_demo.py

"""
Demonstrates SmartLogger rotation logic:
- Size-based rotation
- Time-based rotation
- Combined rotation (size + time)
- Comments explaining daily/weekly behavior
"""
import json
# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

from pathlib import Path
import time

from LogSmith import SmartLogger, stdout
from LogSmith import RotationLogic, When
from LogSmith import LogRecordDetails, OptionalRecordFields

from project_definitions import ROOT_DIR

# ----------------------------------------------------------------------------------------------------------
# 1. Initialization
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()

stdout("\nRotation demo\n=============")

# ----------------------------------------------------------------------------------------------------------
# 2. Prepare log directory and clean old files
# ----------------------------------------------------------------------------------------------------------
stdout("\nPreparing log directory...")

log_dir = Path(ROOT_DIR) / "Logs" / "examples" / "rotation_demo"

# Delete all rotation-related files from previous runs
if log_dir.exists():
    for f in log_dir.iterdir():
        if f.is_file():
            f.unlink()

stdout("Old rotation files removed.")

# ----------------------------------------------------------------------------------------------------------
# 3. Create logger
# ----------------------------------------------------------------------------------------------------------
stdout("\nCreating logger 'rotation_demo'...")

logger = SmartLogger("rotation_demo", level=levels["TRACE"])
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
stdout("\nSize-based rotation (maxBytes=2000)...")

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

stdout("Size-based rotation complete.")

# ==========================================================================================================
# TIME-BASED ROTATION
# ==========================================================================================================
stdout("\nTime-based rotation (rotate every second)...")

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

stdout("Time-based rotation complete.")

# ----------------------------------------------------------------------------------------------------------
# NOTE ABOUT DAILY/WEEKLY ROTATION
# ----------------------------------------------------------------------------------------------------------
stdout("\nDaily/Weekly rotation behavior:")

stdout(
    "- When=When.DAY rotates at midnight local time.\n"
    "- When=When.WEEK rotates at the start of the week (Monday).\n"
    "- interval=N means 'every N days' or 'every N weeks'.\n"
    "- These rotations occur even if the file is small.\n"
)

# ==========================================================================================================
# COMBINED ROTATION (size + time)
# ==========================================================================================================
stdout("\nCombined rotation (maxBytes + time)...")

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

stdout("Combined rotation complete.")

# ----------------------------------------------------------------------------------------------------------
# 5. Show handler_info (JSON-safe)
# ----------------------------------------------------------------------------------------------------------
stdout("\nHandler info:\n-------------")
stdout(json.dumps(logger.handler_info, indent=4))

# ----------------------------------------------------------------------------------------------------------
# 6. SmartLogger rotation safeguards
# ----------------------------------------------------------------------------------------------------------
stdout("\nSmartLogger rotation safeguards:\n--------------------------------")

stdout(
    "- Validates rotation parameters\n"
    "- Prevents invalid combinations (e.g., negative sizes)\n"
    "- Ensures backupCount is respected\n"
    "- Ensures time-based rotation triggers reliably\n"
    "- Ensures size-based rotation triggers immediately when threshold is exceeded\n"
)

stdout("\nRotation demo complete.\n")
