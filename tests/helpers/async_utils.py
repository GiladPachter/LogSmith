import asyncio


async def drain_queue(queue: asyncio.Queue):
    items = []
    while not queue.empty():
        items.append(await queue.get())
    return items
