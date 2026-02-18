# examples/10_removing_handlers_from_loggers.py
import os
import shutil
import time
from pathlib import Path

from project_definitions import ROOT_DIR

from smartlogger import SmartLogger

# ------------------------------------------------------------
# SmartLogger initialization
# ------------------------------------------------------------

levels = SmartLogger.levels()
SmartLogger.initialize_smartlogger(level=levels["INFO"])

# ------------------------------------------------------------
# Setup: two loggers, each with console + file handler
# ------------------------------------------------------------

logger_a = SmartLogger.get("A", level=levels["INFO"])
logger_b = SmartLogger.get("B", level=levels["INFO"])

logger_a.add_console()
logger_b.add_console()

log_dir = (Path(ROOT_DIR) / "logs" / "removing_handlers_demo").resolve()

if os.path.exists(log_dir):
    os.remove(log_dir)

if log_dir.exists():
    shutil.rmtree(log_dir)

logger_a.add_file(log_dir = str(log_dir), logfile_name = "A.log")
logger_b.add_file(log_dir = str(log_dir), logfile_name = "B.log")

# ------------------------------------------------------------
# Step 1: both loggers write 3 INFO entries
# ------------------------------------------------------------

for i in range(1, 4):
    logger_a.info(f"[A] before removal #{i}")
    logger_b.info(f"[B] before removal #{i}")

# ------------------------------------------------------------
# Step 2: remove handlers
# ------------------------------------------------------------

logger_a.remove_file_handler(logfile_name="A.log", log_dir=str(log_dir))
logger_b.remove_console()

# ------------------------------------------------------------
# Step 3: both loggers write 3 more INFO entries
# ------------------------------------------------------------

for i in range(1, 4):
    logger_a.info(f"[A] after removal #{i}")
    logger_b.info(f"[B] after removal #{i}")

# ------------------------------------------------------------
# Step 4: print file contents, indented
# ------------------------------------------------------------

def print_file(label: str, path: Path):
    print(f"\n=== {label} ({path}) ===")
    if not path.exists():
        print("    <file missing>")
        return

    raw = path.read_bytes()
    decoded = raw.decode("utf-8")

    # Print lines
    for line in decoded.splitlines():
        print("    " + line)

    print("\n    NOTE:")
    if label.startswith("Logger A"):
        print("    - Logger A's file is missing the *after removal* lines")
    else:
        print("    - Logger B's file contains all lines (console was removed instead)")

time.sleep(0.1)
print_file("Logger A file", Path(log_dir) / "A.log")
print_file("Logger B file", Path(log_dir) / "B.log")
