# examples/03_file_output_async_demo.py

"""
Demonstrates AsyncSmartLogger file output:
- add_file()
- async rotation basics
- color-preserving file output
- reading ANSI-colored content back from file
- handler_info (JSON-safe)
- AsyncSmartLogger path validation safeguards
"""

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import asyncio
from pathlib import Path

from LogSmith.formatter import LogRecordDetails, OptionalRecordFields
from LogSmith.rotation import RotationLogic, When
from LogSmith.colors import CPrint
from LogSmith.async_smartlogger import AsyncSmartLogger

from project_definitions import ROOT_DIR


async def main():
    print("\nAsync file output demo\n======================")

    # ------------------------------------------------------------------------------------------------------
    # 1. Levels (AsyncSmartLogger does not require global init)
    # ------------------------------------------------------------------------------------------------------
    levels = AsyncSmartLogger.levels()

    # ------------------------------------------------------------------------------------------------------
    # 2. Create logger
    # ------------------------------------------------------------------------------------------------------
    print("\nCreating async logger 'file_demo_async'...")

    logger = AsyncSmartLogger.get("file_demo_async", level=levels["TRACE"])
    logger.add_console(level=levels["TRACE"])   # console for visibility

    # ------------------------------------------------------------------------------------------------------
    # 3. Prepare log directory and clean old files
    # ------------------------------------------------------------------------------------------------------
    print("\nPreparing log directory...")
    await asyncio.sleep(0.1)

    log_dir = Path(ROOT_DIR) / "Logs" / "examples" / "file_demo_async"
    log_dir.mkdir(parents=True, exist_ok=True)

    files_to_delete = [
        "plain_output.log",
        "rotating.log",
        "color_preserved.log",
    ]

    # Delete rotating.log.* as well
    for f in log_dir.iterdir():
        if f.name.startswith("rotating.log"):
            f.unlink()

    for fname in files_to_delete:
        f = log_dir / fname
        if f.exists():
            f.unlink()

    await asyncio.sleep(0.1)
    print("Old demo files removed.")

    # ------------------------------------------------------------------------------------------------------
    # 4. File handler with basic formatting
    # ------------------------------------------------------------------------------------------------------
    print("\nAdding file handler (plain formatting)...")
    await asyncio.sleep(0.1)

    file_details = LogRecordDetails(
        datefmt="%Y-%m-%d %H:%M:%S",
        separator="|",
        optional_record_fields=OptionalRecordFields(
            process_id=True,
            thread_id=True,
            exc_info=True,
            stack_info=True,
        ),
        message_parts_order=[
            "process_id",
            "thread_id",
            "level",
        ],
    )

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="plain_output.log",
        level=levels["TRACE"],
        log_record_details=file_details,
    )

    await logger.a_info("This message goes to both console and file.")

    # ------------------------------------------------------------------------------------------------------
    # 5. Demonstrate rotation basics
    # ------------------------------------------------------------------------------------------------------
    await asyncio.sleep(0.1)
    print("\nAdding rotating file handler...")

    rotation = RotationLogic(
        when=When.SECOND,   # rotate every second
        interval=1,
        maxBytes=5000,      # or size-based rollover
        backupCount=5,
    )

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="rotating.log",
        level=levels["TRACE"],
        rotation_logic=rotation,
    )

    # Show handler info (JSON-safe)
    print(logger.handler_info_json)
    await asyncio.sleep(0.1)

    await logger.a_info("Rotation handler attached.")

    for i in range(20):
        await logger.a_debug(f"Rotating message {i}")

    # ------------------------------------------------------------------------------------------------------
    # 6. Demonstrate color-preserving file output
    # ------------------------------------------------------------------------------------------------------
    await asyncio.sleep(0.1)
    print("\nAdding color-preserving file handler...")

    color_file = log_dir / "color_preserved.log"

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="color_preserved.log",
        level=levels["TRACE"],
        log_record_details=file_details,
        do_not_sanitize_colors_from_string=True,
    )

    print("\nWriting colored text via logger.a_raw():")
    await asyncio.sleep(0.1)

    colored = CPrint.colorize(
        "This text contains ANSI colors",
        fg=CPrint.FG.BRIGHT_MAGENTA
    )

    await logger.a_raw(colored)

    await asyncio.sleep(0.1)
    print("\nEscaped version of colored text (for inspection):")
    print(CPrint.escape_ansi_for_display(colored))

    # ------------------------------------------------------------------------------------------------------
    # 7. Read the color-preserved file back
    # ------------------------------------------------------------------------------------------------------
    print("\nReading color-preserved text back from file:")
    await asyncio.sleep(0.1)

    with open(color_file, "r", encoding="utf-8") as fh:
        file_content = fh.read().rstrip()

    await asyncio.sleep(0.1)
    print("---------------------------------------------")
    print(file_content)
    print("---------------------------------------------")

    print("\nEscaped file content:")
    print(CPrint.escape_ansi_for_display(file_content))

    # ------------------------------------------------------------------------------------------------------
    # 8. Show handler_info (JSON-safe)
    # ------------------------------------------------------------------------------------------------------
    print("\nHandlers details:\n-----------------")
    print(logger.handler_info_json)

    # ------------------------------------------------------------------------------------------------------
    # 9. AsyncSmartLogger safeguards (contextually relevant here)
    # ------------------------------------------------------------------------------------------------------
    print(
        "\nAsyncSmartLogger file-output safeguards:"
        "\n----------------------------------------\n"
        "- log_dir must be an absolute, normalized path (prevents accidental use of relative paths)\n"
        "- log_dir created if not exists\n"
        "- prevents multiple handlers writing to the same file\n"
        "- protects against invalid rotation configurations\n"
        "\n\n"
        "Async file output demo complete."
    )

    # Ensure all logs are flushed before exit
    await logger.flush()


if __name__ == "__main__":
    asyncio.run(main())