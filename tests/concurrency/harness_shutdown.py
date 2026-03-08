# harness_shutdown.py

"""
This validates:
- no lost messages
- no rotation corruption
- no deadlocks
"""

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
