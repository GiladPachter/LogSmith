# examples/04_rotation_async_demo.py

"""
Demonstrates AsyncSmartLogger rotation logic:
- Size-based rotation
- Time-based rotation
- Combined rotation (size + time)
- Notes explaining daily/weekly behavior
"""

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import asyncio
import time
from pathlib import Path

from LogSmith.rotation import RotationLogic, When
from LogSmith.formatter import LogRecordDetails, OptionalRecordFields
from LogSmith.async_smartlogger import AsyncSmartLogger

from project_definitions import ROOT_DIR


async def main():
    print("\nAsync rotation demo\n===================")
    await asyncio.sleep(0.1)

    # ------------------------------------------------------------------------------------------------------
    # 1. Levels (AsyncSmartLogger does not require global init)
    # ------------------------------------------------------------------------------------------------------
    levels = AsyncSmartLogger.levels()

    # ------------------------------------------------------------------------------------------------------
    # 2. Prepare log directory and clean old files
    # ------------------------------------------------------------------------------------------------------
    print("\nPreparing log directory...")

    log_dir = Path(ROOT_DIR) / "Logs" / "examples" / "rotation_async_demo"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Clean previous files
    for f in log_dir.iterdir():
        if f.is_file():
            f.unlink()

    print("Old rotation files removed.")

    # ------------------------------------------------------------------------------------------------------
    # 3. Create logger
    # ------------------------------------------------------------------------------------------------------
    print("\nCreating async logger 'rotation_async_demo'...")
    await asyncio.sleep(0.1)

    logger = AsyncSmartLogger.get("rotation_async_demo", level=levels["TRACE"])
    logger.add_console(level=levels["TRACE"])

    # ------------------------------------------------------------------------------------------------------
    # 4. Common formatting for all file handlers
    # ------------------------------------------------------------------------------------------------------
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

    # ======================================================================================================
    # SIZE-BASED ROTATION
    # ======================================================================================================
    print("\nSize-based rotation (maxBytes=2000)...")
    await asyncio.sleep(0.1)

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="size_based.log",
        level=levels["TRACE"],
        rotation_logic=RotationLogic(
            maxBytes=2000,
            backupCount=5,
        ),
        log_record_details=details,
    )

    for i in range(40):
        await logger.a_info(f"[size] message {i}")

    await asyncio.sleep(0.1)
    print("Size-based rotation complete.")

    # ======================================================================================================
    # TIME-BASED ROTATION
    # ======================================================================================================
    print("\nTime-based rotation (rotate every second)...")
    await asyncio.sleep(0.1)

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="time_based.log",
        level=levels["TRACE"],
        rotation_logic=RotationLogic(
            when=When.SECOND,
            interval=1,
            backupCount=5,
        ),
        log_record_details=details,
    )

    # Write for ~3 seconds to trigger multiple rotations
    start = time.time()
    while time.time() - start < 3:
        await logger.a_debug("[time] rotating...")
        await asyncio.sleep(0.01)  # throttle a bit

    await asyncio.sleep(0.1)
    print("Time-based rotation complete.")

    # ------------------------------------------------------------------------------------------------------
    # NOTE ABOUT DAILY/WEEKLY ROTATION
    # ------------------------------------------------------------------------------------------------------
    print("\nDaily/Weekly rotation behavior:")
    await asyncio.sleep(0.1)

    print(
        "- When=When.EVERYDAY rotates at midnight local time.\n"
        "- When=When.MONDAY ... When.SUNDAY rotate at the start of that weekday.\n"
        "- interval=N means 'every N days' or 'every N weeks'.\n"
        "- These rotations occur even if the file is small.\n"
    )

    # ======================================================================================================
    # COMBINED ROTATION (size + time)
    # ======================================================================================================
    print("\nCombined rotation (maxBytes + time)...")
    await asyncio.sleep(0.1)

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
        await logger.a_warning("[combined] rotating...")
        await asyncio.sleep(0.01)  # throttle a bit

    await asyncio.sleep(0.1)
    print("Combined rotation complete.")

    # ------------------------------------------------------------------------------------------------------
    # 5. Show handler_info (JSON-safe)
    # ------------------------------------------------------------------------------------------------------
    print("\nHandler info:\n-------------")
    print(logger.handler_info_json)

    # ------------------------------------------------------------------------------------------------------
    # 6. AsyncSmartLogger rotation safeguards
    # ------------------------------------------------------------------------------------------------------
    print("\nAsyncSmartLogger rotation safeguards:\n-------------------------------------")

    print(
        "- Validates rotation parameters\n"
        "- Prevents invalid combinations (e.g., negative sizes)\n"
        "- Ensures backupCount is respected\n"
        "- Ensures time-based rotation triggers reliably\n"
        "- Ensures size-based rotation triggers immediately when threshold is exceeded\n"
    )

    print("\nAsync rotation demo complete.\n")

    # Ensure all logs are flushed before exit
    await logger.flush()


if __name__ == "__main__":
    asyncio.run(main())