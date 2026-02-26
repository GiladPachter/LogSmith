# examples/11_misc_issues_demo_async.py

"""
Async counterpart of:
    11_misc_issues_demo.py

Demonstrates AsyncSmartLogger miscellaneous features and safeguards:
- get_record()
- exc_info and stack_info
- retire() and destroy()
- invalid message_parts_order
- invalid log_dir
- invalid rotation logic
- invalid level registration
- invalid theme registration
"""

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import asyncio
import json

from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.formatter import LogRecordDetails, OptionalRecordFields
from LogSmith.rotation import RotationLogic


async def main():
    # ------------------------------------------------------------------------------------------------------
    # 1. Initialization
    # ------------------------------------------------------------------------------------------------------
    levels = AsyncSmartLogger.levels()

    print("\nMiscellaneous AsyncSmartLogger Features\n=======================================")
    await asyncio.sleep(0.1)

    # ------------------------------------------------------------------------------------------------------
    # 2. Create logger with exc_info + stack_info enabled
    # ------------------------------------------------------------------------------------------------------
    print("\nCreating logger 'misc.async'...")
    await asyncio.sleep(0.1)

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
            "level",
            "file_name",
            "lineno",
        ],
        color_all_log_record_fields=True
    )

    logger = AsyncSmartLogger.get("misc.async", level=levels["TRACE"])
    logger.add_console(level=levels["TRACE"], log_record_details=details)

    # ======================================================================================================
    # A. get_record()
    # ======================================================================================================
    print("\nDemonstrating get_record()...")
    await asyncio.sleep(0.1)

    await logger.a_info("This is a test message for get_record()")
    record = logger.get_record(exc_info = True, stack_info = True)

    # Clean stack_info for display
    if record.stack_info:
        record.stack_info = [
            line[2:].replace('"', "'") for line in record.stack_info.splitlines()
        ]

    print("\nRecord contents:")
    await asyncio.sleep(0.1)
    await logger.a_raw(json.dumps(record.__dict__, indent=4))
    await asyncio.sleep(0.1)

    # ======================================================================================================
    # B. exc_info and stack_info
    # ======================================================================================================
    print("\nDemonstrating exc_info and stack_info...\n")
    await asyncio.sleep(0.1)

    try:
        1 / 0
    except ZeroDivisionError:
        record = logger.get_record(exc_info = True, stack_info = True)  # examine record.exc_info if desired
        await logger.a_error("Error with Captured Exception", exc_info=True)

    await logger.a_raw("")
    await logger.a_debug("Debug with Stack Info", stack_info=True)
    await asyncio.sleep(0.1)

    # ======================================================================================================
    # C. retire() and destroy()
    # ======================================================================================================
    print("\nDemonstrating retire() and destroy()...")
    await asyncio.sleep(0.1)

    temp_logger = AsyncSmartLogger.get("temp_logger.async", level=levels["INFO"])
    temp_logger.add_console(level=levels["INFO"])

    await temp_logger.a_info("This logger will be retired.")
    temp_logger.retire()

    print("\nLogger retired. Further handler additions will fail.\n")
    await asyncio.sleep(0.1)

    try:
        temp_logger.add_console()
    except Exception as e:
        print(f"Caught expected error:\n    {type(e).__name__}: {e}")
    await asyncio.sleep(0.1)

    temp_logger.destroy()
    print("\nLogger destroyed. Further usage will fail.")
    await asyncio.sleep(0.1)

    try:
        await temp_logger.a_info("This should fail.")
    except Exception as e:
        print(f"Caught expected error:\n    {type(e).__name__}: {e}")
    await asyncio.sleep(0.1)

    # ======================================================================================================
    # D. Invalid message_parts_order
    # ======================================================================================================
    print("\nTesting invalid message_parts_order...")
    await asyncio.sleep(0.1)

    try:
        LogRecordDetails(
            message_parts_order=["timestamp", "message"],  # forbidden
        )
    except Exception as e:
        print(f"Caught expected error:\n    {type(e).__name__}: {e}")
    await asyncio.sleep(0.1)

    # ======================================================================================================
    # E. Invalid log_dir
    # ======================================================================================================
    print("\nTesting invalid log_dir...")
    await asyncio.sleep(0.1)

    try:
        logger.add_file(log_dir="relative/path/not/allowed")
    except Exception as e:
        print(f"Caught expected error:\n    {type(e).__name__}: {e}")
    await asyncio.sleep(0.1)

    # ======================================================================================================
    # F. Invalid rotation logic
    # ======================================================================================================
    print("\nTesting invalid rotation logic...")
    try:
        RotationLogic(maxBytes=-5)
    except Exception as e:
        print(f"Caught expected error:\n    {type(e).__name__}: {e}")
    await asyncio.sleep(0.1)

    # ======================================================================================================
    # G. Invalid level registration
    # ======================================================================================================
    print("\nTesting invalid level registration...")
    await asyncio.sleep(0.1)

    try:
        AsyncSmartLogger.register_level("INFO", 20)  # duplicate
    except Exception as e:
        print(f"Caught expected error:\n    {type(e).__name__}: {e}")
    await asyncio.sleep(0.1)

    try:
        AsyncSmartLogger.register_level("BAD LEVEL NAME!", 55)  # invalid name
    except Exception as e:
        print(f"Caught expected error:\n    {type(e).__name__}: {e}")
    await asyncio.sleep(0.1)

    # ======================================================================================================
    # H. Invalid theme registration
    # ======================================================================================================
    print("\nTesting invalid theme registration...")
    await asyncio.sleep(0.1)

    try:
        AsyncSmartLogger.apply_color_theme({"INFO": "not a LevelStyle"})
    except Exception as e:
        print(f"Caught expected error:\n    {type(e).__name__}: {e}")
    await asyncio.sleep(0.1)

    # ======================================================================================================
    # I. Summary
    # ======================================================================================================
    print("\nAsyncSmartLogger safeguards demonstrated successfully.\n")
    await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())
