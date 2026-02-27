# examples/05_hierarchy_async_demo.py

"""
Demonstrates AsyncSmartLogger hierarchy behavior:
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

import asyncio

from LogSmith.async_smartlogger import AsyncSmartLogger, a_stdout
from LogSmith.formatter import LogRecordDetails, OptionalRecordFields


async def main():
    await a_stdout("\nAsync hierarchy demo\n====================")

    # ------------------------------------------------------------------------------------------------------
    # 1. Levels (AsyncSmartLogger does not require global init)
    # ------------------------------------------------------------------------------------------------------
    levels = AsyncSmartLogger.levels()

    # ------------------------------------------------------------------------------------------------------
    # 2. Explain hierarchy rules
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nHierarchy rules:")

    await a_stdout(
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

    # ------------------------------------------------------------------------------------------------------
    # 3. Create loggers
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nCreating async loggers...")

    parent     = AsyncSmartLogger("myapp",           level=levels["DEBUG"])
    child      = AsyncSmartLogger("myapp.api",       level=levels["NOTSET"])
    grandchild = AsyncSmartLogger("myapp.api.users", level=levels["NOTSET"])

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

    # ------------------------------------------------------------------------------------------------------
    # Helper: exercise all loggers
    # ------------------------------------------------------------------------------------------------------
    async def exercise():
        await parent.a_debug("parent DEBUG")
        await parent.a_info("parent INFO")

        await child.a_debug("child DEBUG")
        await child.a_info("child INFO")

        await grandchild.a_trace("grandchild TRACE")
        await grandchild.a_debug("grandchild DEBUG")
        await grandchild.a_warning("grandchild WARNING")

    # ------------------------------------------------------------------------------------------------------
    # 4. Demonstrate inheritance
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nInitial behavior (parent = DEBUG, children = NOTSET → inherit DEBUG):")
    await exercise()

    # ------------------------------------------------------------------------------------------------------
    # 5. Change parent level → children inherit new level
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nChanging parent level to INFO...")

    parent.set_level(levels["INFO"])
    await exercise()

    # ------------------------------------------------------------------------------------------------------
    # 6. Change parent level again
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nChanging parent level to TRACE...")

    parent.set_level(levels["TRACE"])
    await exercise()

    # ------------------------------------------------------------------------------------------------------
    # 7. Change parent level to WARNING
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nChanging parent level to WARNING...")

    parent.set_level(levels["WARNING"])
    await exercise()

    await a_stdout("\nAsync hierarchy demo complete.\n")

    # Ensure all logs are flushed before exit
    await parent.flush()
    await child.flush()
    await grandchild.flush()


if __name__ == "__main__":
    asyncio.run(main())