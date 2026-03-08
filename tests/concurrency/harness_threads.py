# harness_threads.py

"""
This is essential for validating thread safety.
"""

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
