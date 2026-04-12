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
import logging
# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import asyncio
import json

from LogSmith import AsyncSmartLogger
from LogSmith import LogRecordDetails, OptionalRecordFields
from LogSmith import RotationLogic


async def main():
    # ------------------------------------------------------------------------------------------------------
    # 1. Initialization
    # ------------------------------------------------------------------------------------------------------
    levels = AsyncSmartLogger.levels()

    print("\nMiscellaneous AsyncSmartLogger Features\n=======================================", flush = True)

    # ------------------------------------------------------------------------------------------------------
    # 2. Create logger with exc_info + stack_info enabled
    # ------------------------------------------------------------------------------------------------------
    print("\nCreating logger 'misc.async'...", flush = True)

    details = LogRecordDetails(
        # datefmt="%Y-%m-%d %H:%M:%S",
        # separator="|",
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

    logger = AsyncSmartLogger("misc_async", level=levels["TRACE"])
    logger.add_console(level=levels["TRACE"], log_record_details=details)

    # ======================================================================================================
    # A. get_record()
    # ======================================================================================================
    await logger.a_stdout("\nDemonstrating get_record()...")

    await logger.a_info("This is a test message for get_record()")
    record = logger.get_record(exc_info = True, stack_info = True)

    # Clean stack_info for display
    if record.stack_info:
        if isinstance(record.stack_info, str):
            record.stack_info = [line[2:].replace('"', "'") for line in record.stack_info.splitlines()]

    await logger.a_stdout("\nRecord contents:")
    await logger.a_raw(logging.INFO, json.dumps(record.__dict__, indent=4))

    # ======================================================================================================
    # B. exc_info and stack_info
    # ======================================================================================================
    await logger.a_stdout("\nDemonstrating exc_info and stack_info...\n")

    try:
        1 / 0
    except ZeroDivisionError:
        record = logger.get_record(exc_info = True, stack_info = True)  # examine record.exc_info if desired
        await logger.a_error("Error with Captured Exception", exc_info=True)

    await logger.a_raw(logging.INFO, "")
    await logger.a_debug("Debug with Stack Info", stack_info=True)

    # ======================================================================================================
    # C. retire() and destroy()
    # ======================================================================================================
    await logger.a_stdout("\nDemonstrating retire() and destroy()...")

    temp_logger = AsyncSmartLogger("temp_logger_async", level=levels["INFO"])
    temp_logger.add_console(level=levels["INFO"])

    await temp_logger.a_info("This logger will be retired.")
    await temp_logger.flush()
    temp_logger.retire()

    await logger.a_stdout("\nLogger retired. Further handler additions will fail.\n")

    try:
        temp_logger.add_console()
    except Exception as e:
        await logger.a_stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

    await temp_logger.destroy()
    await logger.a_stdout("\nLogger destroyed. Further usage will fail.")

    try:
        await temp_logger.a_info("This should fail.")
    except Exception as e:
        await logger.a_stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

    # ======================================================================================================
    # D. Invalid message_parts_order
    # ======================================================================================================
    await logger.a_stdout("\nTesting invalid message_parts_order...")

    try:
        LogRecordDetails(
            message_parts_order=["timestamp", "message"],  # forbidden
        )
    except Exception as e:
        await logger.a_stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

    # ======================================================================================================
    # E. Invalid log_dir
    # ======================================================================================================
    await logger.a_stdout("\nTesting invalid log_dir...")

    try:
        logger.add_file(log_dir="relative/path/not/allowed")
    except Exception as e:
        await logger.a_stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

    # ======================================================================================================
    # F. Invalid rotation logic
    # ======================================================================================================
    await logger.a_stdout("\nTesting invalid rotation logic...")
    try:
        RotationLogic(maxBytes=-5)
    except Exception as e:
        await logger.a_stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

    # ======================================================================================================
    # G. Invalid level registration
    # ======================================================================================================
    await logger.a_stdout("\nTesting invalid level registration...")

    try:
        AsyncSmartLogger.register_level("INFO", 20)  # duplicate
    except Exception as e:
        await logger.a_stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

    try:
        AsyncSmartLogger.register_level("BAD LEVEL NAME!", 55)  # invalid name
    except Exception as e:
        await logger.a_stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

    # ======================================================================================================
    # H. Invalid theme registration
    # ======================================================================================================
    await logger.a_stdout("\nTesting invalid theme registration...")

    try:
        await AsyncSmartLogger.apply_color_theme({"INFO": "not a LevelStyle"})
    except Exception as e:
        await logger.a_stdout(f"Caught expected error:\n    {type(e).__name__}: {e}")

    # ======================================================================================================
    # I. Summary
    # ======================================================================================================
    await logger.a_stdout("\nAsyncSmartLogger safeguards demonstrated successfully.\n")


if __name__ == "__main__":
    asyncio.run(main())
