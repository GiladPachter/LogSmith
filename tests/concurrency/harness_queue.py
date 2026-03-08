# harness_queue.py

"""
This is used to validate:
- no dropped messages
- no deadlocks
- no runaway memory
"""

async def queue_pressure_tester(logger, *, messages: int = 20000):
    """
    Floods the logger queue to test backpressure behavior.
    """

    for i in range(messages):
        await logger.a_info(f"msg {i}")

    await logger.flush()
