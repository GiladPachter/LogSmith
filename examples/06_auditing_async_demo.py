# examples/06_auditing_async_demo.py

"""
Demonstrates AsyncSmartLogger auditing:
- Auditing captures ALL async loggers' output into a single audit file (with rotation)
- Works regardless of each logger's own handlers
- Supports rotation (size, time, or both)
- Shows how to enable and disable auditing cleanly
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
from pathlib import Path
from typing import Dict

from LogSmith import AsyncSmartLogger
from LogSmith import RotationLogic, When
from LogSmith import LogRecordDetails, OptionalRecordFields

from project_definitions import ROOT_DIR


async def main():
    print("\nAsync auditing demo\n===================", flush = True)

    # ------------------------------------------------------------------------------------------------------
    # 1. Levels (AsyncSmartLogger does not require global init)
    # ------------------------------------------------------------------------------------------------------
    levels = AsyncSmartLogger.levels()

    # ------------------------------------------------------------------------------------------------------
    # 2. Prepare audit directory
    # ------------------------------------------------------------------------------------------------------
    print("\nPreparing audit directory...", flush = True)

    audit_dir = Path(ROOT_DIR) / "Logs" / "examples" / "auditing_async_demo"
    audit_dir.mkdir(parents=True, exist_ok=True)

    # Clean previous audit files
    for f in audit_dir.iterdir():
        if f.is_file():
            f.unlink()

    print("Old audit files removed.", flush = True)

    # ------------------------------------------------------------------------------------------------------
    # 3. Create several loggers with different handler setups
    # ------------------------------------------------------------------------------------------------------
    print("\nCreating async loggers...", flush = True)

    loggers: Dict[str, AsyncSmartLogger] = {}

    # 1. console only
    lg1 = AsyncSmartLogger("demo_console_only_async", level=levels["INFO"])
    lg1.add_console(level=levels["INFO"])
    loggers["console_only"] = lg1

    # 2. file only
    lg2 = AsyncSmartLogger("demo_file_only_async", level=levels["INFO"])
    lg2.add_file(
        log_dir=str(audit_dir / "file_only"),
        logfile_name="file_only.log",
        level=levels["INFO"],
    )
    loggers["file_only"] = lg2

    # 3. console + file
    lg3 = AsyncSmartLogger("demo_console_and_file_async", level=levels["INFO"])
    lg3.add_console(level=levels["INFO"])
    lg3.add_file(
        log_dir=str(audit_dir / "console_and_file"),
        logfile_name="console_and_file.log",
        level=levels["INFO"],
    )
    loggers["console_and_file"] = lg3

    # 4. two file handlers
    lg4 = AsyncSmartLogger("demo_two_files_async", level=levels["INFO"])
    lg4.add_file(
        log_dir=str(audit_dir / "two_files_A"),
        logfile_name="A.log",
        level=levels["INFO"],
    )
    lg4.add_file(
        log_dir=str(audit_dir / "two_files_B"),
        logfile_name="B.log",
        level=levels["INFO"],
    )
    loggers["two_files"] = lg4

    await lg1.a_stdout("Async loggers created.")

    # ------------------------------------------------------------------------------------------------------
    # 4. Show logger configurations (JSON-safe)
    # ------------------------------------------------------------------------------------------------------
    await lg1.a_stdout("\nOutput Targets by logger \"<NAME>\":")

    for name, lg in loggers.items():
        await lg.a_stdout(f"\t\"{lg.name}\": ")
        for target in lg.output_targets:
            await lg.a_stdout(f"\t\t{target}")

        await lg.flush()

    # ------------------------------------------------------------------------------------------------------
    # 5. Enable auditing
    # ------------------------------------------------------------------------------------------------------
    audit_details = LogRecordDetails(
        # datefmt="%Y-%m-%d %H:%M:%S",
        # separator="|",
        optional_record_fields=OptionalRecordFields(
            logger_name=True,   # auditing requires this
            lineno=True,
        ),
        message_parts_order=[
            "level",
            "logger_name",
            "lineno",
        ],
    )

    rotation = RotationLogic(
        maxBytes=3000,        # small size to demonstrate rotation
        when=When.SECOND,     # also rotate every second
        interval=1,
        backupCount=5,
    )

    await lg1.a_stdout(f"\nEnabling async auditing of 4 loggers... into '{audit_dir / 'audit.log'}'")

    await AsyncSmartLogger.audit_everything(
        log_dir=str(audit_dir),
        logfile_name="audit.log",
        rotation_logic=rotation,
        details=audit_details,
    )

    await lg1.a_stdout("Auditing enabled.")

    await lg1.flush()
    # await lg2.flush()
    # await lg3.flush()
    # await lg4.flush()


    # ------------------------------------------------------------------------------------------------------
    # 6. Exercise all loggers
    # ------------------------------------------------------------------------------------------------------
    await lg1.a_stdout("\nLogging from all async loggers...")

    for name, lg in loggers.items():
        await lg.a_info(f"[audit] logger '{name}' says hello")
        await lg.a_warning(f"[audit] logger '{name}' warning example")
        await lg.a_error(f"[audit] logger '{name}' error example")

        await lg.flush()

    # ------------------------------------------------------------------------------------------------------
    # 7. Disable auditing
    # ------------------------------------------------------------------------------------------------------
    await lg1.a_stdout("\nActive audit_handler_info:")
    await lg1.a_stdout(json.dumps(AsyncSmartLogger.audit_handler_info(), indent=4))

    await lg1.a_stdout("\nDisabling auditing...")
    await AsyncSmartLogger.terminate_auditing()
    await lg1.a_stdout("Auditing disabled.")

    await lg1.a_stdout("\nDead audit_handler_info:")
    await lg1.a_stdout(json.dumps(AsyncSmartLogger.audit_handler_info(), indent=4))

    # ------------------------------------------------------------------------------------------------------
    # 8. Notes
    # ------------------------------------------------------------------------------------------------------
    await lg1.a_stdout("\nNotes:\n"
          "- To demonstrate size-only rotation: remove 'when' and 'interval'.\n"
          "- To demonstrate time-only rotation: remove 'maxBytes'.\n"
          "- To demonstrate long-term rotation (daily/weekly):\n"
          "      use When.EVERYDAY or When.<WEEKDAY> and adjust timestamp.\n"
          "- Auditing captures ALL async loggers (each logger once), regardless of their own handlers.\n"
          "\n"
          "Async auditing demo complete.\n")

    # Ensure all logs are flushed before exit
    for lg in loggers.values():
        await lg.flush()


if __name__ == "__main__":
    asyncio.run(main())