# examples/02_formatting_demo.py

"""
Demonstrates granular control over log message components:
- OptionalRecordFields (without logger_name)
- message_parts_order
- partial coloring (level + message)
- full-entry coloring (color_all_log_record_fields=True)
- file_name, lineno, func_name in action
"""

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import time

from LogSmith import SmartLogger
from LogSmith import LogRecordDetails, OptionalRecordFields

# ----------------------------------------------------------------------------------------------------------
# 1. Initialization — MUST be done at application entry point
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()
SmartLogger.initialize_smartlogger(level=levels["TRACE"])

print("\nGranular formatting demo\n========================")

# ----------------------------------------------------------------------------------------------------------
# 2. Logger with partial coloring (level + message)
# ----------------------------------------------------------------------------------------------------------
print("\nCreating logger 'granular_partial' (partial coloring)...")
time.sleep(0.1)

lg_partial = SmartLogger.get("granular_partial", level=levels["TRACE"])

partial_details = LogRecordDetails(
    datefmt="%Y-%m-%d %H:%M:%S.%2f",   # milliseconds
    separator="•",
    optional_record_fields=OptionalRecordFields(
        file_name=True,
        lineno=True,
        func_name=True,
    ),
    message_parts_order=[
        "level",      # colored by level style
        "file_name",
        "lineno",
        "func_name",
        # "message",    # colored by level style
    ],
    color_all_log_record_fields=False,  # only level + message are colored
)

lg_partial.add_console(level=levels["TRACE"], log_record_details=partial_details)

def foo():
    lg_partial.info("Function-level log (partial coloring)")

lg_partial.info("Module-level log (func_name = <module>)")
foo()

# ----------------------------------------------------------------------------------------------------------
# 3. Logger with full-entry coloring
# ----------------------------------------------------------------------------------------------------------
time.sleep(0.1)
print("\nCreating logger 'granular_full' (full-entry coloring)...")
time.sleep(0.1)

lg_full = SmartLogger.get("granular_full", level=levels["TRACE"])

full_details = LogRecordDetails(
    datefmt="%Y-%m-%d %H:%M:%S.%2f",
    separator="•",
    optional_record_fields=OptionalRecordFields(
        file_name=True,
        lineno=True,
        func_name=True,
    ),
    message_parts_order=[
        "level",
        "file_name",
        "lineno",
        "func_name",
        # "message",
    ],
    color_all_log_record_fields=True,   # entire entry is colored by level style
)

lg_full.add_console(level=levels["TRACE"], log_record_details=full_details)

def bar():
    lg_full.warning("Function-level log (full-entry coloring)")

lg_full.info("Module-level log (full-entry coloring)")
bar()

time.sleep(0.1)
print("\nGranular formatting demo complete.\n")
