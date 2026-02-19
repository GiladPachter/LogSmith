# examples/08_stress_test.py

"""
Demonstrates SmartLogger under multi-threaded load:
- Thread safety
- Rotation under heavy logging
- Clean, focused, non-duplicative example
"""

# ----------------------------------------------------------------------------------------------------------
# Make ROOT_DIR a known path when executing via CLI from (active) ROOT_DIR
# ----------------------------------------------------------------------------------------------------------
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
# ----------------------------------------------------------------------------------------------------------

import threading
import time
from pathlib import Path

from LogSmith import SmartLogger
from LogSmith import RotationLogic, When
from LogSmith import LogRecordDetails, OptionalRecordFields

from project_definitions import ROOT_DIR

# ----------------------------------------------------------------------------------------------------------
# 1. Initialization — MUST be done at application entry point
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()
SmartLogger.initialize_smartlogger(level=levels["TRACE"])

print("\nStress test demo\n================")

# ----------------------------------------------------------------------------------------------------------
# 2. Prepare log directory
# ----------------------------------------------------------------------------------------------------------
print("\nPreparing log directory...")

log_dir = Path(ROOT_DIR) / "Logs" / "examples" / "stress_test"

# Clean previous files
if log_dir.exists():
    for f in log_dir.iterdir():
        if f.is_file():
            f.unlink()

print("Old stress-test files removed.")

# ----------------------------------------------------------------------------------------------------------
# 3. Create logger
# ----------------------------------------------------------------------------------------------------------
print("\nCreating logger 'stress'...")

logger = SmartLogger.get("stress", level=levels["TRACE"])
logger.add_console(level=levels["TRACE"])

# ----------------------------------------------------------------------------------------------------------
# 4. Add rotating file handler
# ----------------------------------------------------------------------------------------------------------
print("\nAdding rotating file handler...")
time.sleep(0.1)

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

rotation = RotationLogic(
    when=When.SECOND,   # rotate every second
    interval=2,
    maxBytes=50_000,    # or size-based rollover
    backupCount=200,
)

logger.add_file(
    log_dir=str(log_dir),
    logfile_name="stress_test.log",
    level=levels["TRACE"],
    rotation_logic=rotation,
    log_record_details=details,
)

logger.info("Stress-test logger ready.")
time.sleep(0.1)

# ----------------------------------------------------------------------------------------------------------
# 5. Worker thread
# ----------------------------------------------------------------------------------------------------------
def worker(thread_Number: int, iterations: int):
    for i in range(iterations):
        logger.info(f"[thread number {thread_Number}] message {i}")

# ----------------------------------------------------------------------------------------------------------
# 6. Stress test runner
# ----------------------------------------------------------------------------------------------------------
def run_stress_test(thread_count: int = 32, iterations_per_thread: int = 5000):
    print(f"\nStarting stress test with {thread_count} threads...")
    time.sleep(0.1)

    threads = [
        threading.Thread(
            target=worker,
            args=(t, iterations_per_thread),
            daemon=True,
        )
        for t in range(thread_count)
    ]

    start = time.time()

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    end = time.time()

    print(f"\nStress test completed in {end - start:.2f} seconds")
    time.sleep(0.1)

# ----------------------------------------------------------------------------------------------------------
# 7. Entry point
# ----------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    run_stress_test()

    time.sleep(0.1)
    print("\nStress test demo complete.\n")
