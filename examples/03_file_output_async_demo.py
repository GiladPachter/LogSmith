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

from LogSmith import LogRecordDetails, OptionalRecordFields
from LogSmith import RotationLogic, When
from LogSmith import CPrint
from LogSmith import AsyncSmartLogger, a_stdout

from project_definitions import ROOT_DIR


async def main():
    await a_stdout("\nAsync file output demo\n======================")

    # ------------------------------------------------------------------------------------------------------
    # 1. Levels (AsyncSmartLogger does not require global init)
    # ------------------------------------------------------------------------------------------------------
    levels = AsyncSmartLogger.levels()

    # ------------------------------------------------------------------------------------------------------
    # 2. Create logger
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nCreating async logger 'file_demo_async'...")

    logger = AsyncSmartLogger("file_demo_async", level=levels["TRACE"])
    logger.add_console(level=levels["TRACE"])   # console for visibility

    # ------------------------------------------------------------------------------------------------------
    # 3. Prepare log directory and clean old files
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nPreparing log directory...")

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

    await a_stdout("Old demo files removed.")

    # ------------------------------------------------------------------------------------------------------
    # 4. File handler with basic formatting
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nAdding file handler (plain formatting)...")

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
    await a_stdout("\nAdding rotating file handler...")

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
    await a_stdout(json.dumps(logger.handler_info, indent=4))

    await logger.a_info("Rotation handler attached.")

    for i in range(20):
        await logger.a_debug(f"Rotating message {i}")

    # ------------------------------------------------------------------------------------------------------
    # 6. Demonstrate color-preserving file output
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nAdding color-preserving file handler...")

    color_file = log_dir / "color_preserved.log"

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="color_preserved.log",
        level=levels["TRACE"],
        log_record_details=file_details,
        do_not_sanitize_colors_from_string=True,
    )

    await a_stdout("\nWriting colored text via logger.a_raw():")

    colored = CPrint.colorize(
        "This text contains ANSI colors",
        fg=CPrint.FG.BRIGHT_MAGENTA
    )

    await logger.a_raw(colored)

    await a_stdout("\nEscaped version of colored text (for inspection):")
    await a_stdout(CPrint.escape_ansi_for_display(colored))

    # ------------------------------------------------------------------------------------------------------
    # 7. Read the color-preserved file back
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nReading color-preserved text back from file:")

    with open(color_file, "r", encoding="utf-8") as fh:
        file_content = fh.read().rstrip()

    await a_stdout("---------------------------------------------")
    await a_stdout(file_content)
    await a_stdout("---------------------------------------------")

    await a_stdout("\nEscaped file content:")
    await a_stdout(CPrint.escape_ansi_for_display(file_content))

    # ------------------------------------------------------------------------------------------------------
    # 8. Show handler_info (JSON-safe)
    # ------------------------------------------------------------------------------------------------------
    await a_stdout("\nHandlers details:\n-----------------")
    await a_stdout(json.dumps(logger.handler_info, indent=4))

    # ------------------------------------------------------------------------------------------------------
    # 9. AsyncSmartLogger safeguards (contextually relevant here)
    # ------------------------------------------------------------------------------------------------------
    await a_stdout(
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