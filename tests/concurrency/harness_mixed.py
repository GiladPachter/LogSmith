# harness_mixed.py

"""
This simulates real‑world mixed workloads.
"""

import asyncio
import threading

from LogSmith import AsyncSmartLogger


async def mixed_flooder(
    logger: AsyncSmartLogger,
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
        await logger.a_info("sync message")

    # Wait for async tasks
    await asyncio.gather(*async_jobs)

    # Wait for threads
    for t in thread_jobs:
        t.join()
