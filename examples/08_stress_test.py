# examples/08_stress_test.py

"""
Demonstrates SmartLogger under multi-threaded load:
- Thread safety
- Rotation under heavy logging
- Live progress bar (imported from async demo style)
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

from LogSmith import SmartLogger, stdout
from LogSmith import RotationLogic, When
from LogSmith import LogRecordDetails, OptionalRecordFields

from project_definitions import ROOT_DIR


# ----------------------------------------------------------------------------------------------------------
# 1. Initialization
# ----------------------------------------------------------------------------------------------------------
levels = SmartLogger.levels()

stdout("\nStress test demo\n================")


# ----------------------------------------------------------------------------------------------------------
# 2. Prepare log directory
# ----------------------------------------------------------------------------------------------------------
stdout("\nPreparing log directory...")

log_dir = Path(ROOT_DIR) / "Logs" / "examples" / "stress_test"

# Clean previous files
if log_dir.exists():
    for f in log_dir.iterdir():
        if f.is_file():
            f.unlink()

stdout("Old stress-test files removed.")


# ----------------------------------------------------------------------------------------------------------
# 3. Create logger
# ----------------------------------------------------------------------------------------------------------
stdout("\nCreating logger 'stress'...")

logger = SmartLogger("stress", level=levels["TRACE"])
# logger.add_console(level=levels["TRACE"])


# ----------------------------------------------------------------------------------------------------------
# 4. Add rotating file handler
# ----------------------------------------------------------------------------------------------------------
stdout("\nAdding rotating file handler...")

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


# ----------------------------------------------------------------------------------------------------------
# 5. Worker thread
# ----------------------------------------------------------------------------------------------------------
def worker(thread_number: int, iterations: int, progress_dict, lock):
    for i in range(iterations):
        logger.info(f"[thread number {thread_number}] message {i}")

        # update progress counter
        with lock:
            progress_dict["count"] += 1


# ----------------------------------------------------------------------------------------------------------
# 6. Progress bar monitor (threaded)
# ----------------------------------------------------------------------------------------------------------
def start_progress_monitor(total_messages, progress_dict, lock):
    bar_width = 40
    start_time = time.time()

    def monitor():
        while True:
            time.sleep(0.2)

            with lock:
                done = progress_dict["count"]

            pct = done / total_messages
            filled = int(pct * bar_width)
            bar = "█" * filled + "-" * (bar_width - filled)     #   Alt+219 = "█"   (filled progress-bar character)

            elapsed = time.time() - start_time
            rate = done / elapsed if elapsed > 0 else 0
            eta = (total_messages - done) / rate if rate > 0 else 0

            stdout(
                f"\r[{bar}] {pct*100:5.1f}%  "
                f"done={done}/{total_messages}  "
                f"{rate:7.1f} msg/s  "
                f"ETA {eta:5.1f}s",
                end="",
            )

            if done >= total_messages:
                break

        stdout()  # newline after finishing

    t = threading.Thread(target=monitor, daemon=True)
    t.start()
    return t


# ----------------------------------------------------------------------------------------------------------
# 7. Stress test runner
# ----------------------------------------------------------------------------------------------------------
def run_stress_test(thread_count: int = 32, iterations_per_thread: int = 5000):
    stdout(f"\nStarting stress test with {thread_count} threads and {5000} logs per thread...")
    stdout(f"(Writing logs to: '{logger.handler_info[0]["path"]}')")


    total_messages = thread_count * iterations_per_thread

    progress = {"count": 0}
    lock = threading.Lock()

    # Start progress monitor
    monitor_thread = start_progress_monitor(total_messages, progress, lock)

    threads = [
        threading.Thread(
            target=worker,
            args=(t, iterations_per_thread, progress, lock),
            daemon=True,
        )
        for t in range(thread_count)
    ]

    start = time.time()

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    monitor_thread.join()

    end = time.time()

    stdout(f"\nStress test completed in {end - start:.2f} seconds")


# ----------------------------------------------------------------------------------------------------------
# 8. Entry point
# ----------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    run_stress_test()

    stdout("\nStress test demo complete.\n")