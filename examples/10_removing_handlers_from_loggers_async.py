# examples/10_removing_handlers_from_loggers_async.py

"""
Async counterpart of:
    10_removing_handlers_from_loggers.py

Demonstrates:
- Adding console + file handlers
- Removing handlers at runtime
- Verifying results by reading files
"""

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import os
import shutil
import asyncio
from pathlib import Path

from project_definitions import ROOT_DIR

from LogSmith.async_smartlogger import AsyncSmartLogger


async def print_file(label: str, path: Path):
    print(f"\n=== {label} ({path}) ===")
    if not path.exists():
        print("    <file missing>")
        return

    raw = path.read_bytes()
    decoded = raw.decode("utf-8")

    for line in decoded.splitlines():
        print("    " + line)

    print("\n    NOTE:")
    if label.startswith("Logger A"):
        print("    - Logger A's file is missing the *after removal* lines")
    else:
        print("    - Logger B's file contains all lines (console was removed instead)")


async def main():
    # ------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------
    levels = AsyncSmartLogger.levels()
    # AsyncSmartLogger.initialize_(level=levels["INFO"])

    # ------------------------------------------------------------
    # Setup: two loggers, each with console + file handler
    # ------------------------------------------------------------
    logger_a = AsyncSmartLogger.get("A", level=levels["INFO"])
    logger_b = AsyncSmartLogger.get("B", level=levels["INFO"])

    logger_a.add_console()
    logger_b.add_console()

    log_dir = (Path(ROOT_DIR) / "logs" / "examples" / "removing_handlers_demo_async").resolve()

    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)

    logger_a.add_file(log_dir=str(log_dir), logfile_name="A.log")
    logger_b.add_file(log_dir=str(log_dir), logfile_name="B.log")

    # ------------------------------------------------------------
    # Step 1: both loggers write 3 INFO entries
    # ------------------------------------------------------------
    for i in range(1, 4):
        await logger_a.a_info(f"[A] before removal #{i}")
        await logger_b.a_info(f"[B] before removal #{i}")

    # ------------------------------------------------------------
    # Step 2: remove handlers
    # ------------------------------------------------------------
    await logger_a.flush()
    await logger_b.flush()

    logger_a.remove_file_handler(logfile_name="A.log", log_dir=str(log_dir))
    logger_b.remove_console()

    # ------------------------------------------------------------
    # Step 3: both loggers write 3 more INFO entries
    # ------------------------------------------------------------
    for i in range(1, 4):
        await logger_a.a_info(f"[A] after removal #{i}")
        await logger_b.a_info(f"[B] after removal #{i}")

    # Ensure all logs are written
    await logger_a.flush()
    await logger_b.flush()

    # ------------------------------------------------------------
    # Step 4: print file contents
    # ------------------------------------------------------------
    await print_file("Logger A file", Path(log_dir) / "A.log")
    await print_file("Logger B file", Path(log_dir) / "B.log")


if __name__ == "__main__":
    asyncio.run(main())