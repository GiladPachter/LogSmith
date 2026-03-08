# File: LogSmith/temp/generate_concurrency_tests.py
# Run this script once to generate the full concurrency test suite.

import os
from pathlib import Path

TARGET_DIR = Path(__file__).resolve().parent.parent / "tests" / "concurrency"
TARGET_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------
# Helper function to write files
# -------------------------------------------------------------------
def write(name: str, content: str):
    path = TARGET_DIR / name
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] wrote {path}")


# ===================================================================
# 1. harness_async.py
# ===================================================================
write("harness_async.py", r'''
import asyncio

async def async_task_flooder(
    logger,
    message: str,
    *,
    tasks: int = 10,
    messages_per_task: int = 1000,
    delay: float | None = None,
):
    """
    Spawns N async tasks, each logging M messages.
    Optional delay between messages to simulate realistic load.
    """

    async def worker():
        for _ in range(messages_per_task):
            await logger.a_info(message)
            if delay:
                await asyncio.sleep(delay)

    await asyncio.gather(*(worker() for _ in range(tasks)))
''')


# ===================================================================
# 2. harness_threads.py
# ===================================================================
write("harness_threads.py", r'''
import threading
import asyncio

def thread_flooder(
    logger,
    loop: asyncio.AbstractEventLoop,
    message: str,
    *,
    threads: int = 5,
    messages_per_thread: int = 2000,
):
    """
    Spawns T threads, each logging K messages via run_coroutine_threadsafe.
    """

    def worker():
        for _ in range(messages_per_thread):
            asyncio.run_coroutine_threadsafe(
                logger.a_info(message),
                loop,
            )

    thread_list = [threading.Thread(target=worker) for _ in range(threads)]
    for t in thread_list:
        t.start()
    for t in thread_list:
        t.join()
''')


# ===================================================================
# 3. harness_mixed.py
# ===================================================================
write("harness_mixed.py", r'''
import asyncio
import threading

async def mixed_flooder(
    logger,
    loop,
    *,
    async_tasks: int = 5,
    async_messages: int = 500,
    threads: int = 5,
    thread_messages: int = 500,
    sync_messages: int = 500,
):
    """
    Mixes async logging, thread logging, and synchronous logging.
    """

    async def async_worker():
        for _ in range(async_messages):
            await logger.a_info("async message")

    def thread_worker():
        for _ in range(thread_messages):
            asyncio.run_coroutine_threadsafe(
                logger.a_info("thread message"),
                loop,
            )

    # Start async tasks
    async_jobs = [async_worker() for _ in range(async_tasks)]

    # Start threads
    thread_jobs = [threading.Thread(target=thread_worker) for _ in range(threads)]
    for t in thread_jobs:
        t.start()

    # Sync logging
    for _ in range(sync_messages):
        logger.info("sync message")

    # Wait for async tasks
    await asyncio.gather(*async_jobs)

    # Wait for threads
    for t in thread_jobs:
        t.join()
''')


# ===================================================================
# 4. harness_rotation.py
# ===================================================================
write("harness_rotation.py", r'''
from pathlib import Path

def inspect_rotation(log_dir: Path, base_name: str):
    """
    Returns:
        base_exists: bool
        rotated_files: list[Path]
        rotation_numbers: list[int]
    """

    base_file = log_dir / base_name

    rotated = [
        p for p in log_dir.iterdir()
        if p.name.startswith(base_name + ".") and not p.name.endswith(".lock")
    ]

    rotation_numbers = []
    for p in rotated:
        suffix = p.name.split(".")[-1]
        if suffix.isdigit():
            rotation_numbers.append(int(suffix))

    return base_file.exists(), rotated, sorted(rotation_numbers)
''')


# ===================================================================
# 5. harness_queue.py
# ===================================================================
write("harness_queue.py", r'''
import asyncio

async def queue_pressure_tester(logger, *, messages: int = 20000):
    """
    Floods the logger queue to test backpressure behavior.
    """

    for i in range(messages):
        await logger.a_info(f"msg {i}")

    await logger.flush()
''')


# ===================================================================
# 6. harness_shutdown.py
# ===================================================================
write("harness_shutdown.py", r'''
import asyncio
import random

async def shutdown_race_tester(logger, *, messages: int = 5000):
    """
    Logs heavily and triggers shutdown at a random moment.
    """

    async def spammer():
        for i in range(messages):
            await logger.a_info(f"msg {i}")
            if random.random() < 0.0005:
                break

    spam_task = asyncio.create_task(spammer())

    # Random delay before shutdown
    await asyncio.sleep(random.uniform(0.01, 0.2))

    await logger.shutdown()
    await spam_task
''')


# ===================================================================
# 7. test_async_concurrency.py
# ===================================================================
write("test_async_concurrency.py", r'''
import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic
from .harness_async import async_task_flooder

def test_async_concurrency(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        logger = AsyncSmartLogger("async.concurrent", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(str(log_dir), "app.log")

        await async_task_flooder(logger, "hello", tasks=10, messages_per_task=500)

        await logger.flush()
        await logger.shutdown()

        assert (log_dir / "app.log").exists()

    asyncio.run(main())
''')


# ===================================================================
# 8. test_thread_concurrency.py
# ===================================================================
write("test_thread_concurrency.py", r'''
import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic
from .harness_threads import thread_flooder

def test_thread_concurrency(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        logger = AsyncSmartLogger("thread.concurrent", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(str(log_dir), "app.log")

        loop = asyncio.get_running_loop()

        thread_flooder(logger, loop, "thread msg", threads=5, messages_per_thread=1000)

        await logger.flush()
        await logger.shutdown()

        assert (log_dir / "app.log").exists()

    asyncio.run(main())
''')


# ===================================================================
# 9. test_mixed_concurrency.py
# ===================================================================
write("test_mixed_concurrency.py", r'''
import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic
from .harness_mixed import mixed_flooder

def test_mixed_concurrency(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        logger = AsyncSmartLogger("mixed.concurrent", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(str(log_dir), "app.log")

        loop = asyncio.get_running_loop()

        await mixed_flooder(logger, loop)

        await logger.flush()
        await logger.shutdown()

        assert (log_dir / "app.log").exists()

    asyncio.run(main())
''')


# ===================================================================
# 10. test_rotation_concurrency.py
# ===================================================================
write("test_rotation_concurrency.py", r'''
import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from LogSmith.rotation import RotationLogic
from .harness_async import async_task_flooder
from .harness_rotation import inspect_rotation

def test_rotation_concurrency(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        rotation = RotationLogic(maxBytes=2000, backupCount=5)

        logger = AsyncSmartLogger("rotate.concurrent", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(str(log_dir), "app.log", rotation_logic=rotation)

        await async_task_flooder(logger, "rotation test", tasks=10, messages_per_task=1000)

        await logger.flush()
        await logger.shutdown()

        base_exists, rotated, numbers = inspect_rotation(log_dir, "app.log")

        assert base_exists
        assert len(rotated) >= 1
        assert numbers == sorted(numbers)

    asyncio.run(main())
''')


# ===================================================================
# 11. test_queue_pressure.py
# ===================================================================
write("test_queue_pressure.py", r'''
import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from .harness_queue import queue_pressure_tester

def test_queue_pressure(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        logger = AsyncSmartLogger("queue.pressure", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(str(log_dir), "app.log")

        await queue_pressure_tester(logger, messages=15000)

        await logger.flush()
        await logger.shutdown()

        assert (log_dir / "app.log").exists()

    asyncio.run(main())
''')


# ===================================================================
# 12. test_shutdown_race.py
# ===================================================================
write("test_shutdown_race.py", r'''
import asyncio
from pathlib import Path
from LogSmith import AsyncSmartLogger
from .harness_shutdown import shutdown_race_tester

def test_shutdown_race(tmp_path: Path):
    async def main():
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        logger = AsyncSmartLogger("shutdown.race", level=AsyncSmartLogger.levels()["INFO"])
        logger.add_file(str(log_dir), "app.log")

        await shutdown_race_tester(logger)

        # shutdown_race_tester already calls shutdown()

        assert (log_dir / "app.log").exists()

    asyncio.run(main())
''')


print("\nAll concurrency tests generated successfully.")
