# LogSmith/file_registry.py

import threading
from pathlib import Path

class FileHandlerRegistry:
    __lock = threading.RLock()
    __active_paths: set[str] = set()

    @classmethod
    def register(cls, path: str) -> None:
        normalized = str(Path(path).resolve())
        with cls.__lock:
            if normalized in cls.__active_paths:
                raise ValueError(
                    f"LogSmith: file handler for '{normalized}' is already active "
                    f"in this process (SmartLogger or AsyncSmartLogger)."
                )
            cls.__active_paths.add(normalized)

    @classmethod
    def unregister(cls, path: str) -> None:
        normalized = str(Path(path).resolve())
        with cls.__lock:
            cls.__active_paths.discard(normalized)
