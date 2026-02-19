# examples/05_hierarchy_demo.py

"""
Demonstrates SmartLogger hierarchy behavior:
- Parent → child → grandchild
- NOTSET inheritance
- Changing parent level affects descendants
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

print("\nHierarchy demo\n==============")
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 2. Explain hierarchy rules
# ----------------------------------------------------------------------------------------------------------
print("\nHierarchy rules:")
time.sleep(0.1)

print(
    "  - Logger names define hierarchy via dot notation\n"
    "      parent\n"
    "      parent.child\n"
    "      parent.child.grandchild\n\n"
    "  - Level inheritance:\n"
    "      • If a logger has its own level → use it\n"
    "      • If level is NOTSET → inherit from parent\n"
    "      • If parent is NOTSET → inherit from grandparent\n"
    "      • Ultimately falls back to root logger level\n"
)
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 3. Create loggers
# ----------------------------------------------------------------------------------------------------------
print("\nCreating loggers...")
time.sleep(0.1)

parent     = SmartLogger.get("myapp",           level=levels["DEBUG"])
child      = SmartLogger.get("myapp.api",       level=levels["NOTSET"])
grandchild = SmartLogger.get("myapp.api.users", level=levels["NOTSET"])

# All loggers share the same formatting
details = LogRecordDetails(
    datefmt="%Y-%m-%d %H:%M:%S.%2f",
    separator="•",
    optional_record_fields=OptionalRecordFields(
        logger_name=True,   # hierarchy demo requires this
    ),
    message_parts_order=[
        "level",
        "logger_name",
    ],
    color_all_log_record_fields=True,
)

parent.add_console(level=levels["TRACE"], log_record_details=details)
child.add_console(level=levels["TRACE"], log_record_details=details)
grandchild.add_console(level=levels["TRACE"], log_record_details=details)


# ----------------------------------------------------------------------------------------------------------
# Helper: exercise all loggers
# ----------------------------------------------------------------------------------------------------------
def exercise():
    parent.debug("parent DEBUG")
    parent.info("parent INFO")

    child.debug("child DEBUG")
    child.info("child INFO")

    grandchild.trace("grandchild TRACE")
    grandchild.debug("grandchild DEBUG")
    grandchild.warning("grandchild WARNING")


# ----------------------------------------------------------------------------------------------------------
# 4. Demonstrate inheritance
# ----------------------------------------------------------------------------------------------------------
print("\nInitial behavior (parent = DEBUG, children = NOTSET → inherit DEBUG):")
time.sleep(0.1)
exercise()
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 5. Change parent level → children inherit new level
# ----------------------------------------------------------------------------------------------------------
print("\nChanging parent level to INFO...")
time.sleep(0.1)

parent.setLevel(levels["INFO"])
exercise()
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 6. Change parent level again
# ----------------------------------------------------------------------------------------------------------
print("\nChanging parent level to TRACE...")
time.sleep(0.1)

parent.setLevel(levels["TRACE"])
exercise()
time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------
# 7. Change parent level to WARNING
# ----------------------------------------------------------------------------------------------------------
print("\nChanging parent level to WARNING...")
time.sleep(0.1)

parent.setLevel(levels["WARNING"])
exercise()
time.sleep(0.1)


print("\nHierarchy demo complete.\n")
