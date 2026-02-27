# examples/11_misc_issues_demo.py

"""
Demonstrates SmartLogger miscellaneous features and safeguards:
- get_record()
- exc_info and stack_info (actually shown)
- retire() and destroy()
- invalid message_parts_order
- invalid log_dir
- invalid rotation logic
- invalid level registration
- invalid theme registration
- SmartLogger safeguards in action
"""

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import json

from LogSmith import SmartLogger, stdout
from LogSmith import LogRecordDetails, OptionalRecordFields
from LogSmith import RotationLogic

# ----------------------------------------------------------------------------------------------------------
# 1. Initialization
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()

stdout("\nMiscellaneous SmartLogger Features\n=================================")

# ----------------------------------------------------------------------------------------------------------
# 2. Create logger with exc_info + stack_info enabled
# ----------------------------------------------------------------------------------------------------------
stdout("\nCreating logger 'misc'...")

details = LogRecordDetails(
    datefmt="%Y-%m-%d %H:%M:%S",
    separator="|",
    optional_record_fields=OptionalRecordFields(
        file_name=True,
        lineno=True,
        exc_info=True,
        stack_info=True,
    ),
    message_parts_order=[
        "level",      # colored by level style
        "file_name",
        "lineno",
    ],
    color_all_log_record_fields=True
)

logger = SmartLogger("misc", level=levels["TRACE"])
logger.add_console(level=levels["TRACE"], log_record_details=details)

# ==========================================================================================================
# A. get_record()
# ==========================================================================================================
stdout("\nDemonstrating get_record()...")

logger.info("This is a test message for get_record()")
record = SmartLogger.get_record()
if isinstance(record.stack_info, str):
    record.stack_info = [line[2:].replace('"', "'") for line in record.stack_info.splitlines()]
stdout("\nRecord contents:")
logger.raw(json.dumps(record.__dict__, indent=4))

# ==========================================================================================================
# B. exc_info and stack_info (now visible)
# ==========================================================================================================
stdout("\nDemonstrating exc_info and stack_info...\n")

try:
    1 / 0
except ZeroDivisionError:
    # ---------------------------
    record = SmartLogger.get_record()    # examine record.exc_info at your convenience
    # ---------------------------
    logger.error("Error with Captured Exception", exc_info=True)

logger.raw("")

logger.debug("Debug with Stack Info", stack_info=True)

# ==========================================================================================================
# C. retire() and destroy()
# ==========================================================================================================
stdout("\nDemonstrating retire() and destroy()...")

temp_logger = SmartLogger("temp_logger", level=levels["INFO"])
temp_logger.add_console(level=levels["INFO"])

temp_logger.info("This logger will be retired.")
temp_logger.retire()

stdout("\nLogger retired. Further handler additions will fail.\n")

try:
    temp_logger.add_console()
except Exception as e:
    stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

temp_logger.destroy()
stdout("\n\nLogger destroyed. Further usage will fail.")

try:
    temp_logger.info("This should fail.")
except Exception as e:
    stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

# ==========================================================================================================
# D. Invalid message_parts_order
# ==========================================================================================================
stdout("\nTesting invalid message_parts_order...")

try:
    LogRecordDetails(
        message_parts_order=["timestamp", "message"],  # forbidden
    )
except Exception as e:
    stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

# ==========================================================================================================
# E. Invalid log_dir
# ==========================================================================================================
stdout("\nTesting invalid log_dir...")

try:
    logger.add_file(log_dir="relative/path/not/allowed")
except Exception as e:
    stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

# ==========================================================================================================
# F. Invalid rotation logic
# ==========================================================================================================
stdout("\nTesting invalid rotation logic...")
try:
    RotationLogic(maxBytes=-5)  # invalid
except Exception as e:
    stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

# ==========================================================================================================
# G. Invalid level registration
# ==========================================================================================================
stdout("\nTesting invalid level registration...")

try:
    SmartLogger.register_level("INFO", 20)  # duplicate
except Exception as e:
    stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

try:
    SmartLogger.register_level("BAD LEVEL NAME!", 55)  # invalid name
except Exception as e:
    stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

# ==========================================================================================================
# H. Invalid theme registration
# ==========================================================================================================
stdout("\nTesting invalid theme registration...")

try:
    SmartLogger.apply_color_theme({"INFO": "not a LevelStyle"})
except Exception as e:
    stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

# ==========================================================================================================
# I. Summary
# ==========================================================================================================
stdout("\nSmartLogger safeguards demonstrated successfully.\n")
