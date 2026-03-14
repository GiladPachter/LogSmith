# LogSmith/file_registry.py

import threading
from pathlib import Path

class FileHandlerRegistry:
    _lock = threading.RLock()
    _active_paths: set[str] = set()

    @classmethod
    def register(cls, path: str) -> None:
        normalized = str(Path(path).resolve())
        with cls._lock:
            if normalized in cls._active_paths:
                raise ValueError(
                    f"LogSmith: file handler for '{normalized}' is already active "
                    f"in this process (SmartLogger or AsyncSmartLogger)."
                )
            cls._active_paths.add(normalized)

    @classmethod
    def unregister(cls, path: str) -> None:
        normalized = str(Path(path).resolve())
        with cls._lock:
            cls._active_paths.discard(normalized)
