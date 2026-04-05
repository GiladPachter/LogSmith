# examples/02_formatting_async_demo.py

"""
Demonstrates granular control over async log message components:
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

import asyncio

from LogSmith import LogRecordDetails, OptionalRecordFields
from LogSmith import AsyncSmartLogger


async def main():
    print("\nGranular async formatting demo\n==============================", flush = True)

    levels = AsyncSmartLogger.levels()

    # ------------------------------------------------------------------------------------------------------
    # 2. Logger with partial coloring (level + message)
    # ------------------------------------------------------------------------------------------------------
    print("\nCreating async logger 'granular_partial_async' (partial coloring)...", flush = True)

    lg_partial = AsyncSmartLogger("granular_partial_async", level=levels["TRACE"])

    partial_details = LogRecordDetails(
        datefmt="%Y-%m-%d %H:%M:%S.%2f",   # milliseconds
        separator="•",
        optional_record_fields=OptionalRecordFields(
            file_name=True,
            lineno=True,
            func_name=True,
        ),
        message_parts_order=[
            "level",        # required for positioning
            "file_name",
            "lineno",
            "func_name",    # colored by level style
        ],
        color_all_log_record_fields=False,  # only level + message are colored
    )

    lg_partial.add_console(level=levels["TRACE"], log_record_details=partial_details)

    async def foo():
        await lg_partial.a_info("Function-level log (partial coloring)")

    await lg_partial.a_info("Module-level log (func_name = <module>)")
    await foo()

    await lg_partial.flush()

    # ------------------------------------------------------------------------------------------------------
    # 3. Logger with full-entry coloring
    # ------------------------------------------------------------------------------------------------------
    print("\nCreating async logger 'granular_full_async' (full-entry coloring)...", flush = True)

    lg_full = AsyncSmartLogger("granular_full_async", level=levels["TRACE"])

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

    async def bar():
        await lg_full.a_warning("Function-level log (full-entry coloring)")

    await lg_full.a_info("Module-level log (full-entry coloring)")
    await bar()

    await lg_full.flush()

    print("\nGranular async formatting demo complete.\n", flush = True)


if __name__ == "__main__":
    asyncio.run(main())