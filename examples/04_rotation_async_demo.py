# examples/04_rotation_async_demo.py

"""
Demonstrates AsyncSmartLogger rotation logic:
- Size-based rotation
- Time-based rotation
- Combined rotation (size + time)
- Notes explaining daily/weekly behavior
"""
import json
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

from LogSmith import RotationLogic, When
from LogSmith import LogRecordDetails, OptionalRecordFields
from LogSmith import AsyncSmartLogger, a_stdout

from project_definitions import ROOT_DIR


async def main():
    await a_stdout("\nAsync rotation demo\n===================")

    # ------------------------------------------------------------------------------------------------------
    # 1. Levels (AsyncSmartLogger does not require global init)
    # ------------------------------------------------------------------------------------------------------
    levels = AsyncSmartLogger.levels()

    # ------------------------------------------------------------------------------------------------------
    # 2. Prepare log directory and clean old files
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nPreparing log directory...")

    log_dir = Path(ROOT_DIR) / "Logs" / "examples" / "rotation_async_demo"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Clean previous files
    for f in log_dir.iterdir():
        if f.is_file():
            f.unlink()

    await a_stdout("Old rotation files removed.")

    # ------------------------------------------------------------------------------------------------------
    # 3. Create logger
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nCreating async logger 'rotation_async_demo'...")

    logger = AsyncSmartLogger("rotation_async_demo", level=levels["TRACE"])
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
    await a_stdout("\nSize-based rotation (maxBytes=2000)...")

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

    await a_stdout("Size-based rotation complete.")

    # ======================================================================================================
    # TIME-BASED ROTATION
    # ======================================================================================================
    await a_stdout("\nTime-based rotation (rotate every second)...")

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

    await a_stdout("Time-based rotation complete.")

    # ------------------------------------------------------------------------------------------------------
    # NOTE ABOUT DAILY/WEEKLY ROTATION
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nDaily/Weekly rotation behavior:")

    await a_stdout(
        "- When=When.EVERYDAY rotates at midnight local time.\n"
        "- When=When.MONDAY ... When.SUNDAY rotate at the start of that weekday.\n"
        "- interval=N means 'every N days' or 'every N weeks'.\n"
        "- These rotations occur even if the file is small.\n"
    )

    # ======================================================================================================
    # COMBINED ROTATION (size + time)
    # ======================================================================================================
    await a_stdout("\nCombined rotation (maxBytes + time)...")

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

    await a_stdout("Combined rotation complete.")

    # ------------------------------------------------------------------------------------------------------
    # 5. Show handler_info (JSON-safe)
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nHandler info:\n-------------")
    await a_stdout(json.dumps(logger.handler_info, indent=4))

    # ------------------------------------------------------------------------------------------------------
    # 6. AsyncSmartLogger rotation safeguards
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nAsyncSmartLogger rotation safeguards:\n-------------------------------------")

    await a_stdout(
        "- Validates rotation parameters\n"
        "- Prevents invalid combinations (e.g., negative sizes)\n"
        "- Ensures backupCount is respected\n"
        "- Ensures time-based rotation triggers reliably\n"
        "- Ensures size-based rotation triggers immediately when threshold is exceeded\n"
    )

    await a_stdout("\nAsync rotation demo complete.\n")

    # Ensure all logs are flushed before exit
    await logger.flush()


if __name__ == "__main__":
    asyncio.run(main())