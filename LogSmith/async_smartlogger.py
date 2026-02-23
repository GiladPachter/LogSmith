# LogSmith/async_smartlogger.py

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Optional, Union

from .smartlogger import SmartLogger, RetrievedRecord
from .formatter import LogRecordDetails
from .levels import TRACE, LevelStyle


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
                    return
                level, msg, args, kwargs = item
                if level == "RAW":
                    await asyncio.to_thread(self._logger.raw, msg, **kwargs)
                else:
                    # noinspection PyProtectedMember
                    await asyncio.to_thread(self._logger._log, level, msg, args, **kwargs)

            finally:
                self._queue.task_done()

    # ------------------------------------------------------------
    # Hybrid API: synchronous enqueue helper
    # ------------------------------------------------------------
    def _enqueue_sync(self, level: Union[int, str], msg: str, args: tuple, kwargs: dict) -> None:
        if self._stopped:
            raise RuntimeError("AsyncSmartLogger has been shut down.")

        try:
            # If we're already inside the event loop thread:
            if asyncio.get_running_loop() is self._loop:
                # Enqueue immediately
                self._queue.put_nowait((level, msg, args, kwargs))
                return
        except RuntimeError:
            # Not in an event loop → fall through to thread-safe scheduling
            pass

        # Called from outside the loop → schedule thread-safe
        self._loop.call_soon_threadsafe(
            lambda: self._queue.put_nowait((level, msg, args, kwargs))
        )

    # ------------------------------------------------------------
    # Synchronous logging API (no await)
    # ------------------------------------------------------------
    def trace(self, msg: str, *args: Any, **kwargs: Any) -> None:
        extra = kwargs.pop("extra", {})
        extra.update(kwargs)
        self._enqueue_sync(TRACE, msg, args, {"extra": extra})

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        extra = kwargs.pop("extra", {})
        extra.update(kwargs)
        self._enqueue_sync(logging.DEBUG, msg, args, {"extra": extra})

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        extra = kwargs.pop("extra", {})
        extra.update(kwargs)
        self._enqueue_sync(logging.INFO, msg, args, {"extra": extra})

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        extra = kwargs.pop("extra", {})
        extra.update(kwargs)
        self._enqueue_sync(logging.WARNING, msg, args, {"extra": extra})

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        extra = kwargs.pop("extra", {})
        extra.update(kwargs)
        self._enqueue_sync(logging.ERROR, msg, args, {"extra": extra})

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        extra = kwargs.pop("extra", {})
        extra.update(kwargs)
        self._enqueue_sync(logging.CRITICAL, msg, args, {"extra": extra})

    def raw(self, message: str, end: str = "\n") -> None:
        self._enqueue_sync("RAW", message, (), {"end": end})

    # ------------------------------------------------------------
    # Asynchronous logging API (awaitable)
    # ------------------------------------------------------------
    async def a_log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        if self._stopped:
            raise RuntimeError("AsyncSmartLogger has been shut down.")

        extra = kwargs.pop("extra", {})
        extra.update(kwargs)
        await self._queue.put((level, msg, args, {"extra": extra}))

    async def a_trace(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.a_log(TRACE, msg, *args, **kwargs)

    async def a_debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.a_log(logging.DEBUG, msg, *args, **kwargs)

    async def a_info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.a_log(logging.INFO, msg, *args, **kwargs)

    async def a_warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.a_log(logging.WARNING, msg, *args, **kwargs)

    async def a_error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.a_log(logging.ERROR, msg, *args, **kwargs)

    async def a_critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.a_log(logging.CRITICAL, msg, *args, **kwargs)

    async def a_raw(self, message: str, end: str = "\n") -> None:
        await self._queue.put(("RAW", message, (), {"end": end}))

    # ------------------------------------------------------------
    # Handler passthroughs
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

        await self._queue.join()
        await self._queue.put(self._SENTINEL)

        if self._worker_task is not None:
            await self._worker_task

    # ------------------------------------------------------------
    # Level registry helpers
    # ------------------------------------------------------------
    @staticmethod
    def levels() -> dict[str, int]:
        return SmartLogger.levels()

    @staticmethod
    def __safeguard_internals(name: str):
        if name in AsyncSmartLogger.__dict__:
            raise ValueError(f"Cannot override internal AsyncSmartLogger attribute '{name}'")

    @staticmethod
    def register_level(name: str, value: int, style: Optional[LevelStyle] = None) -> None:
        AsyncSmartLogger.__safeguard_internals(name)
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