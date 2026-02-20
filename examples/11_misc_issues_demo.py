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

import time
import json
from pathlib import Path

from LogSmith import SmartLogger
from LogSmith import LogRecordDetails, OptionalRecordFields
from LogSmith import RotationLogic, When

# ----------------------------------------------------------------------------------------------------------
# JSON-safe serializer
# ----------------------------------------------------------------------------------------------------------
def safe(obj):
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if hasattr(obj, "name"):
        return obj.name
    if isinstance(obj, dict):
        return {k: safe(v) for k, v in obj.items()}
    return str(obj)

# ----------------------------------------------------------------------------------------------------------
# 1. Initialization — MUST be done at application entry point
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()
SmartLogger.initialize_smartlogger(level=levels["TRACE"])

print("\nMiscellaneous SmartLogger Features\n=================================")
time.sleep(0.1)

# ----------------------------------------------------------------------------------------------------------
# 2. Create logger with exc_info + stack_info enabled
# ----------------------------------------------------------------------------------------------------------
print("\nCreating logger 'misc'...")
time.sleep(0.1)

details = LogRecordDetails(
    datefmt="%Y-%m-%d %H:%M:%S",
    separator="|",
    optional_record_fields=OptionalRecordFields(
        exc_info=True,
        stack_info=True,
    ),
    message_parts_order=None,   # REQUIRED when only diagnostics are enabled
)

logger = SmartLogger.get("misc", level=levels["TRACE"])
logger.add_console(level=levels["TRACE"], log_record_details=details)

# ==========================================================================================================
# A. get_record()
# ==========================================================================================================
print("\nDemonstrating get_record()...")
time.sleep(0.1)

logger.info("This is a test message for get_record()")
record = logger.get_record()
record.stack_info = [line[2:].replace('"', "'") for line in record.stack_info.splitlines()]

print("\nRecord contents:")
time.sleep(0.1)
logger.raw(json.dumps(record.__dict__, indent=4))
time.sleep(0.1)

# ==========================================================================================================
# B. exc_info and stack_info (now visible)
# ==========================================================================================================
print("\nDemonstrating exc_info and stack_info...\n")
time.sleep(0.1)

try:
    1 / 0
except ZeroDivisionError:
    logger.error("Error with Captured Exception", exc_info=True)

logger.raw("")

logger.debug("Debug with Stack Info", stack_info=True)
time.sleep(0.1)

# ==========================================================================================================
# C. retire() and destroy()
# ==========================================================================================================
print("\nDemonstrating retire() and destroy()...")
time.sleep(0.1)

temp_logger = SmartLogger.get("temp_logger", level=levels["INFO"])
temp_logger.add_console(level=levels["INFO"])

temp_logger.info("This logger will be retired.")
temp_logger.retire()

print("\nLogger retired. Further handler additions will fail.\n")
time.sleep(0.1)

try:
    temp_logger.add_console()
except Exception as e:
    print(f"Caught expected error:\n    {type(e).__name__}: {e}")
time.sleep(0.1)

temp_logger.destroy()
print("\n\nLogger destroyed. Further usage will fail.")
time.sleep(0.1)

try:
    temp_logger.info("This should fail.")
except Exception as e:
    print(f"Caught expected error:\n    {type(e).__name__}: {e}")
time.sleep(0.1)

# ==========================================================================================================
# D. Invalid message_parts_order
# ==========================================================================================================
print("\nTesting invalid message_parts_order...")
time.sleep(0.1)

try:
    LogRecordDetails(
        message_parts_order=["timestamp", "message"],  # forbidden
    )
except Exception as e:
    print(f"Caught expected error:\n    {type(e).__name__}: {e}")
time.sleep(0.1)

# ==========================================================================================================
# E. Invalid log_dir
# ==========================================================================================================
print("\nTesting invalid log_dir...")
time.sleep(0.1)

try:
    logger.add_file(log_dir="relative/path/not/allowed")
except Exception as e:
    print(f"Caught expected error:\n    {type(e).__name__}: {e}")
time.sleep(0.1)

# ==========================================================================================================
# F. Invalid rotation logic
# ==========================================================================================================
print("\nTesting invalid rotation logic...")
try:
    RotationLogic(maxBytes=-5)  # invalid
except Exception as e:
    print(f"Caught expected error:\n    {type(e).__name__}: {e}")
time.sleep(0.1)

# ==========================================================================================================
# G. Invalid level registration
# ==========================================================================================================
print("\nTesting invalid level registration...")
time.sleep(0.1)

try:
    SmartLogger.register_level("INFO", 20)  # duplicate
except Exception as e:
    print(f"Caught expected error:\n    {type(e).__name__}: {e}")
time.sleep(0.1)

try:
    SmartLogger.register_level("BAD LEVEL NAME!", 55)  # invalid name
except Exception as e:
    print(f"Caught expected error:\n    {type(e).__name__}: {e}")
time.sleep(0.1)

# ==========================================================================================================
# H. Invalid theme registration
# ==========================================================================================================
print("\nTesting invalid theme registration...")
time.sleep(0.1)

try:
    SmartLogger.apply_color_theme({"INFO": "not a LevelStyle"})
except Exception as e:
    print(f"Caught expected error:\n    {type(e).__name__}: {e}")
time.sleep(0.1)

# ==========================================================================================================
# I. Summary
# ==========================================================================================================
print("\nSmartLogger safeguards demonstrated successfully.\n")
time.sleep(0.1)
