# LogSmith/async_smartlogger.py

import asyncio
import inspect
import logging
from typing import Any, Optional, Callable, Awaitable, Union

from .smartlogger import SmartLogger, RetrievedRecord
from .formatter import LogRecordDetails
from .levels import TRACE, LevelStyle


# Type for items in the queue: either a log tuple or a sentinel
class _Sentinel:
    pass


QueueItem = Union[
    tuple[int, str, tuple, dict[str, Any]],
    _Sentinel,
]


class AsyncSmartLogger:
    _SENTINEL = _Sentinel()

    @staticmethod
    def _allowed_callers():
        return {
            ("LogSmith.async_smartlogger", "get"),
        }

    @staticmethod
    def _called_from_allowed() -> bool:
        allowed = AsyncSmartLogger._allowed_callers()

        for frame_info in inspect.stack()[2:8]:
            frame = frame_info.frame
            module = frame.f_globals.get("__name__")
            func = frame_info.function

            if (module, func) in allowed:
                return True

        return False

    def __init__(self, inner: SmartLogger) -> None:
        if not AsyncSmartLogger._called_from_allowed():
            raise RuntimeError(
                "AsyncSmartLogger cannot be instantiated directly. "
                "Use AsyncSmartLogger.get(name, level)."
            )

        self._loop = asyncio.get_running_loop()
        self._logger = inner
        self._queue: asyncio.Queue[QueueItem] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task[None]] = None
        self._stopped = False
        self._start_worker()

    @classmethod
    def get(cls, name: str, level: int) -> "AsyncSmartLogger":
        # Enforce reserved-name rule at async layer too
        # if name == "root":
        #     raise ValueError("AsyncSmartLogger cannot wrap a logger named 'root'. Choose a different name.")
        inner = SmartLogger.get(name, level)
        return cls(inner)

    # ------------------------------------------------------------
    # Worker lifecycle
    # ------------------------------------------------------------
    def _start_worker(self) -> None:
        if self._worker_task is not None:
            return
        self._worker_task = self._loop.create_task(self._worker())

    async def _worker(self) -> None:
        while True:
            item = await self._queue.get()
            try:
                if isinstance(item, _Sentinel):
                    return  # exit the worker
                level, msg, args, kwargs = item
                await asyncio.to_thread(self._logger._log, level, msg, args, **kwargs)
            finally:
                self._queue.task_done()

    # ------------------------------------------------------------
    # Public async logging API
    # ------------------------------------------------------------
    async def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        if self._stopped:
            raise RuntimeError("AsyncSmartLogger has been shut down.")
        await self._queue.put((level, msg, args, kwargs))

    async def trace(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.log(TRACE, msg, *args, **kwargs)

    async def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.log(logging.DEBUG, msg, *args, **kwargs)

    async def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.log(logging.INFO, msg, *args, **kwargs)

    async def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.log(logging.WARNING, msg, *args, **kwargs)

    async def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.log(logging.ERROR, msg, *args, **kwargs)

    async def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.log(logging.CRITICAL, msg, *args, **kwargs)

    async def raw(self, message: str, end: str = "\n") -> None:
        if self._stopped:
            raise RuntimeError("AsyncSmartLogger has been shut down.")
        await asyncio.to_thread(self._logger.raw, message, end=end)

    # ------------------------------------------------------------
    # Handler management passthroughs
    # ------------------------------------------------------------
    def add_console(self, *args: Any, **kwargs: Any) -> None:
        self._logger.add_console(*args, **kwargs)

    def add_file(self, *args: Any, **kwargs: Any) -> None:
        self._logger.add_file(*args, **kwargs)

    def remove_console(self) -> None:
        self._logger.remove_console()

    def remove_file_handler(self, logfile_name: str, log_dir: str) -> None:
        self._logger.remove_file_handler(logfile_name, log_dir)

    @property
    def handler_info_json(self) -> str:
        return self._logger.handler_info_json

    @property
    def output_targets(self) -> list[str]:
        return self._logger.output_targets

    @property
    def handler_info(self):
        return self._logger.handler_info

    @property
    def file_handlers(self):
        return self._logger.file_handlers

    @property
    def console_handler(self):
        return self._logger.console_handler

    # ------------------------------------------------------------
    # Flush
    # ------------------------------------------------------------
    async def flush(self) -> None:
        """
        Drain all pending log records but keep the logger alive.
        """
        if self._stopped:
            raise RuntimeError("AsyncSmartLogger has been shut down.")
        await self._queue.join()

    # ------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------
    async def shutdown(self) -> None:
        if self._stopped:
            return
        self._stopped = True

        # Wait for all real log records to be processed
        await self._queue.join()

        # Send sentinel to wake the worker and let it exit
        await self._queue.put(self._SENTINEL)

        # Wait for the worker to finish
        if self._worker_task is not None:
            await self._worker_task

    # ------------------------------------------------------------
    # Level registry helpers
    # ------------------------------------------------------------
    @staticmethod
    def levels() -> dict[str, int]:
        return SmartLogger.levels()

    @staticmethod
    def register_level(name: str, value: int, style: Optional[LevelStyle] = None) -> None:
        SmartLogger.register_level(name, value, style)

    @staticmethod
    def apply_color_theme(theme: dict[int, LevelStyle] | None) -> None:
        SmartLogger.apply_color_theme(theme)

    # ------------------------------------------------------------
    # Life cycle
    # ------------------------------------------------------------
    def retire(self) -> None:
        self._logger.retire()

    def destroy(self) -> None:
        self._logger.destroy()

    # ------------------------------------------------------------
    # Auditing
    # ------------------------------------------------------------
    @staticmethod
    def audit_everything(*args: Any, **kwargs: Any) -> None:
        SmartLogger.audit_everything(*args, **kwargs)

    @staticmethod
    def terminate_auditing() -> None:
        SmartLogger.terminate_auditing()

    # ------------------------------------------------------------
    # Record inspection
    # ------------------------------------------------------------
    async def get_record(self) -> RetrievedRecord:
        return await asyncio.to_thread(self._logger.get_record)

    async def get_record_parts(self) -> RetrievedRecord:
        return await asyncio.to_thread(self._logger.get_record_parts)