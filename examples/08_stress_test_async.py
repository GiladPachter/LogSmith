# examples/08_stress_test_async.py

"""
Async stress test with:
- High‑volume async logging
- Rotation
- Progress bar
- Throughput metrics
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import asyncio
import time
from pathlib import Path

from LogSmith import AsyncSmartLogger, a_stdout
from LogSmith import RotationLogic, When
from LogSmith import LogRecordDetails, OptionalRecordFields

from project_definitions import ROOT_DIR


async def main():
    levels = AsyncSmartLogger.levels()

    await a_stdout("\nAsync Stress Test demo\n======================")

    # --------------------------------------------------------------
    # Prepare log directory
    # --------------------------------------------------------------
    await a_stdout("\nPreparing log directory...")

    log_dir = Path(ROOT_DIR) / "Logs" / "examples" / "stress_test_async"
    if log_dir.exists():
        for f in log_dir.iterdir():
            if f.is_file():
                f.unlink()

    await a_stdout("Old stress-test files removed.")

    # --------------------------------------------------------------
    # Create logger
    # --------------------------------------------------------------
    await a_stdout("\nCreating async logger 'stress.async'...")

    logger = AsyncSmartLogger("stress.async", level=levels["TRACE"])
    # logger.add_console(level=levels["TRACE"])

    # --------------------------------------------------------------
    # Rotating file handler
    # --------------------------------------------------------------
    await a_stdout("\nAdding rotating file handler...")

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
        when=When.SECOND,
        interval=2,
        maxBytes=50_000,
        backupCount=200,
    )

    logger.add_file(
        log_dir=str(log_dir),
        logfile_name="stress_test_async.log",
        level=levels["TRACE"],
        rotation_logic=rotation,
        log_record_details=details,
    )

    await logger.a_info("Async stress-test logger ready.")

    # --------------------------------------------------------------
    # Stress test parameters
    # --------------------------------------------------------------
    TASK_COUNT = 16
    ITERATIONS = 2000
    TOTAL = TASK_COUNT * ITERATIONS

    # Shared progress counter
    progress = {"count": 0}
    lock = asyncio.Lock()

    # --------------------------------------------------------------
    # Worker coroutine
    # --------------------------------------------------------------
    async def worker(worker_id: int):
        for i in range(ITERATIONS):
            await logger.a_info(f"[worker {worker_id}] message {i}")

            # update progress counter
            async with lock:
                progress["count"] += 1

            if i % 50 == 0:
                await asyncio.sleep(0.02)

    # --------------------------------------------------------------
    # Progress monitor
    # --------------------------------------------------------------
    async def monitor():
        bar_width = 40
        start_time = time.time()

        while True:
            await asyncio.sleep(0.2)

            async with lock:
                done = AsyncSmartLogger.messages_processed()
                backlog = logger.queue_depth()

            pct = done / TOTAL
            filled = int(pct * bar_width)
            bar = "█" * filled + "-" * (bar_width - filled)     #   Alt+219 = "█"   (filled progress-bar character)

            elapsed = time.time() - start_time
            rate = done / elapsed if elapsed > 0 else 0
            eta = (TOTAL - done) / rate if rate > 0 else 0

            await a_stdout(
                f"\r[{bar}] {pct*100:5.1f}%  "
                f"done={done}/{TOTAL}  "
                f"backlog={backlog}  "
                f"{rate:7.1f} msg/s  "
                f"ETA {eta:5.1f}s",
                end="",
            )

            if done >= TOTAL:
                break

        await a_stdout()  # newline after progress bar

    # --------------------------------------------------------------
    # Run workers + monitor
    # --------------------------------------------------------------
    await a_stdout(f"\nStarting async stress test with {TASK_COUNT} tasks...\n")

    start = time.time()

    tasks = [asyncio.create_task(worker(t)) for t in range(TASK_COUNT)]
    monitor_task = asyncio.create_task(monitor())

    await asyncio.gather(*tasks)
    await monitor_task

    # --------------------------------------------------------------
    # Flush logger
    # --------------------------------------------------------------
    await logger.flush()

    end = time.time()
    await a_stdout(f"\nStress test completed in {end - start:.2f} seconds\n")


if __name__ == "__main__":
    asyncio.run(main())
