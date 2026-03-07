import threading
from pathlib import Path
from typing import Callable


def hammer_logger(fn: Callable[[], None], threads: int = 10, iterations: int = 100):
    def worker():
        for _ in range(iterations):
            fn()

    ts = [threading.Thread(target=worker) for _ in range(threads)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0
