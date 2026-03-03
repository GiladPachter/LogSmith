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

from LogSmith import SmartLogger, stdout
from LogSmith import LogRecordDetails, OptionalRecordFields


# ----------------------------------------------------------------------------------------------------------
# 1. Initialization
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()

stdout("\nHierarchy demo\n==============")

# ----------------------------------------------------------------------------------------------------------
# 2. Explain hierarchy rules
# ----------------------------------------------------------------------------------------------------------
stdout("\nHierarchy rules:")

stdout(
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

# ----------------------------------------------------------------------------------------------------------
# 3. Create loggers
# ----------------------------------------------------------------------------------------------------------
stdout("\nCreating loggers...")

parent     = SmartLogger("myapp",           level=levels["DEBUG"])
child      = SmartLogger("myapp.api",       level=levels["NOTSET"])
grandchild = SmartLogger("myapp.api.users", level=levels["NOTSET"])

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
stdout("\nInitial behavior (parent = DEBUG, children = NOTSET → inherit DEBUG):")
exercise()

# ----------------------------------------------------------------------------------------------------------
# 5. Change parent level → children inherit new level
# ----------------------------------------------------------------------------------------------------------
stdout("\nChanging parent level to INFO...")

parent.set_level(levels["INFO"])
exercise()

# ----------------------------------------------------------------------------------------------------------
# 6. Change parent level again
# ----------------------------------------------------------------------------------------------------------
stdout("\nChanging parent level to TRACE...")

parent.set_level(levels["TRACE"])
exercise()

# ----------------------------------------------------------------------------------------------------------
# 7. Change parent level to WARNING
# ----------------------------------------------------------------------------------------------------------
stdout("\nChanging parent level to WARNING...")

parent.set_level(levels["WARNING"])
exercise()

stdout("\nHierarchy demo complete.\n")
