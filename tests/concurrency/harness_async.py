# harness_async.py

"""
This is the backbone of async concurrency testing.
"""

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
