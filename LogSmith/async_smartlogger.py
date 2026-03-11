# LogSmith/async_smartlogger.py

from __future__ import annotations

import asyncio
import logging
import multiprocessing
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, ClassVar, Optional
import os
import threading
import time

from .formatter import (
    StructuredPlainFormatter,
    StructuredColorFormatter,
    PassthroughFormatter,
    AuditFormatter,
    LogRecordDetails, OutputMode, StructuredJSONFormatter, StructuredNDJSONFormatter,
)
from .levels import TRACE, LevelStyle
from .level_registry import LEVELS
from .colors import CPrint
from .rotation import RotationLogic
from .async_rotation import Async_TimedSizedRotatingFileHandler
from .smartlogger import RetrievedRecord, HandlerMetadata

"""
console printing utility
"stdout()" function replaces print()
it has the same effect, only it synchronizes with console logs
"""
import io
import contextlib


class AsyncOp(Enum):
    LOG = auto()
    RAW = auto()
    ROTATE = auto()
    SENTINEL = auto()


@dataclass
class _QueueItem:
    op: AsyncOp
    payload: dict[str, Any]


import sys
import inspect


class AsyncSmartLogger:
    """
    AsyncSmartLogger
    =================
    A fully asynchronous logging engine, independent of SmartLogger.

    • Async-only API (a_debug, a_info, a_error, a_raw, etc.)
    • Uses logging.Logger internally (composition, not inheritance)
    • Uses its own async-capable handlers (e.g. Async_TimedSizedRotatingFileHandler)
    • Shares formatter utilities and rotation primitives with SmartLogger
    • Supports TRACE and dynamically registered levels
    """

    __default_level: ClassVar[int] = logging.INFO

    # auditing state
    __audit_enabled: ClassVar[bool] = False
    __audit_logger: ClassVar[Optional["AsyncSmartLogger"]] = None
    __audit_handler: ClassVar[Optional[logging.Handler]] = None

    __messages_processed: ClassVar[int] = 0

    @classmethod
    def messages_processed(cls) -> int:
        return cls.__messages_processed

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    # ------------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------------
    def __init__(self, name: str, level: int) -> None:
        self._name = name

        self._py_logger = logging.getLogger(name)
        self._py_logger.propagate = False

        if level == logging.NOTSET:
            self._py_logger.setLevel(logging.NOTSET)
        else:
            self._py_logger.setLevel(level)

        self._loop = asyncio.get_running_loop()
        self._queue: asyncio.Queue[_QueueItem] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task[None]] = None
        self._stopped = False

        self._handlers: list[HandlerMetadata] = []
        self._real_handlers: list[logging.Handler] = []

        self._messages_enqueued = 0

        self._retired = False

        self.__start_worker()

        # =====================================

        self._profile_enabled = False
        self._profile_stats = {
            "count": 0,
            "find_caller": 0.0,
            "record": 0.0,
            "handlers": 0.0,
            "total": 0.0,
        }

    def enable_profiling(self, enable: bool):
        self._profile_enabled = enable

    def get_profiling_details(self) -> str:
        if not self._profile_enabled:
            return "Profiling not enabled."

        c = self._profile_stats["count"]
        if c == 0:
            return "No profiling data collected."

        profiling_details = (f"Total log events: {c}\n"
                             f"Avg find_caller: {self._profile_stats['find_caller'] / c * 1e6:.2f} µs\n"
                             f"Avg record creation: {self._profile_stats['record'] / c * 1e6:.2f} µs\n"
                             f"Avg handler time: {self._profile_stats['handlers'] / c * 1e6:.2f} µs\n"
                             f"Avg total per log: {self._profile_stats['total'] / c * 1e6:.2f} µs\n"
                             )

        return profiling_details

    # ------------------------------------------------------------------
    # WORKER
    # ------------------------------------------------------------------
    def __start_worker(self, workers: int = 1):
        if hasattr(self, "_worker_tasks"):
            return  # pragma: no cover
        self._worker_tasks = [
            self._loop.create_task(self.__worker())
            for _ in range(workers)
        ]

    async def __worker(self) -> None:
        while True:
            item = await self._queue.get()
            try:
                if item.op is AsyncOp.SENTINEL:
                    return  # pragma: no cover

                if item.op is AsyncOp.LOG:
                    await self.__process_log(item.payload)
                elif item.op is AsyncOp.RAW:
                    await self.__process_raw(item.payload)
                elif item.op is AsyncOp.ROTATE:
                    await self.__process_rotate(item.payload)
            finally:
                self._queue.task_done()

    # ------------------------------------------------------------------
    # PROCESS LOG
    # ------------------------------------------------------------------
    async def __process_log(self, payload: dict[str, Any]) -> None:
        level: int = payload["level"]
        msg: str = payload["msg"]
        args: tuple[Any, ...] = payload["args"]
        extra: dict[str, Any] = payload["extra"]
        fields: dict[str, Any] = payload["fields"]
        exc_info = payload["exc_info"]
        stack_info_flag: bool = payload["stack_info_flag"]

        if fields:
            extra.setdefault("fields", {}).update(fields)

        if self._profile_enabled:
            t0 = time.perf_counter()

        if self._profile_enabled:
            t1 = time.perf_counter()
        # =========================
        frame = self.__find_caller()
        # =========================
        if self._profile_enabled:
            # noinspection PyUnboundLocalVariable
            self._profile_stats["find_caller"] += time.perf_counter() - t1

        pathname = payload["pathname"]
        lineno = payload["lineno"]
        func_name = payload["func_name"]

        sinfo = "".join(traceback.format_stack()) if stack_info_flag else None

        # AUDIT
        if (
            AsyncSmartLogger.__audit_enabled
            and AsyncSmartLogger.__audit_logger is not None
            and AsyncSmartLogger.__audit_logger is not self
        ):
            audit_extra = extra.copy()
            audit_extra.setdefault("fields", {}).update(fields)
            audit_extra["force_logger_name"] = self._name

            await AsyncSmartLogger.__audit_logger._enqueue_log(
                level,
                msg,
                args,
                audit_extra,
                {},  # no additional fields
                exc_info=None,
                stack_info_flag=False,
                pathname=pathname,  # 🔹 forward original caller info
                lineno=lineno,
                func_name=func_name,
            )

        record_name = extra.pop("force_logger_name", self._name)

        if self._profile_enabled:
            t1 = time.perf_counter()
        # =========================
        record = logging.LogRecord(
            name=record_name,
            level=level,
            pathname=pathname,
            lineno=lineno,
            msg=msg,
            args=args,
            exc_info=exc_info,
            func=func_name,
            sinfo=sinfo,
        )
        # =========================
        if self._profile_enabled:
            self._profile_stats["record"] += time.perf_counter() - t1

        record.__dict__.update(extra)

        if self._profile_enabled:
            t1 = time.perf_counter()
        # ======================================
        for handler in self._py_logger.handlers:
            formatter = handler.formatter

            # JSON / NDJSON: offload formatting, then write
            if isinstance(formatter, (StructuredJSONFormatter, StructuredNDJSONFormatter)):
                formatted = await asyncio.to_thread(formatter.format, record)
                stream = getattr(handler, "stream", None)
                # Reopen if missing OR closed
                if (stream is None or getattr(stream, "closed", False)) and hasattr(handler, "_open"):
                    try:
                        handler.acquire()
                        # noinspection PyProtectedMember
                        handler.stream = handler._open()
                    finally:
                        handler.release()
                    stream = handler.stream

                if stream is None:
                    continue

                if isinstance(handler, Async_TimedSizedRotatingFileHandler):
                    # Protect file rotation + writes
                    with handler.write_lock:
                        stream.write(formatted + "\n")
                        stream.flush()
                else:
                    # Console / plain file handlers
                    stream.write(formatted + "\n")
                    stream.flush()

            else:
                # Non-JSON handlers: only lock rotating file handlers
                if isinstance(handler, Async_TimedSizedRotatingFileHandler):
                    with handler.write_lock:
                        handler.emit(record)
                else:
                    handler.emit(record)
        # ======================================
        if self._profile_enabled:
            self._profile_stats["handlers"] += time.perf_counter() - t1

        if self._profile_enabled:
            # noinspection PyUnboundLocalVariable
            self._profile_stats["total"] += time.perf_counter() - t0
            self._profile_stats["count"] += 1


        AsyncSmartLogger.__messages_processed += 1

    # ------------------------------------------------------------------
    # PROCESS RAW
    # ------------------------------------------------------------------
    async def __process_raw(self, payload: dict[str, Any]) -> None:
        message: str = payload["message"]
        end: str = payload["end"]

        for handler in self._py_logger.handlers:
            stream = getattr(handler, "stream", None)

            # FIX: Reopen file handler stream if needed
            if stream is None and hasattr(handler, "baseFilename"):
                try:
                    handler.acquire()
                    # noinspection PyUnresolvedReferences,PyProtectedMember
                    handler.stream = handler._open()
                finally:
                    handler.release()
                stream = handler.stream

            # Still no stream? Skip
            if stream is None:
                continue

            is_console = isinstance(handler, logging.StreamHandler) and not hasattr(handler, "baseFilename")

            if is_console:
                text = self.__bleach_non_colored_text(message)
            else:
                do_not_sanitize = getattr(handler, "do_not_sanitize_colors_from_string", False)
                text = message if do_not_sanitize else CPrint.strip_ansi(message)

            # noinspection PyBroadException
            try:
                stream.write(text + end)
                stream.flush()
            except Exception:   # pragma: no cover
                # Ignore write errors
                pass    # pragma: no cover

    # ------------------------------------------------------------------
    # PROCESS ROTATION
    # ------------------------------------------------------------------
    @staticmethod
    async def __process_rotate(payload: dict[str, Any]) -> None:
        handler: Async_TimedSizedRotatingFileHandler = payload["handler"]
        with handler.write_lock:
            await asyncio.to_thread(handler.perform_rotation)

    # ------------------------------------------------------------------
    # CALLER RESOLUTION
    # ------------------------------------------------------------------
    @staticmethod
    def __find_caller():
        frame = inspect.currentframe().f_back  # caller of __find_caller

        while frame:
            filename = frame.f_code.co_filename.replace("\\", "/")
            base = os.path.basename(filename)

            # Skip ONLY the actual SmartLogger implementation file
            if base != "async_smartlogger.py" and not (
                    os.path.basename(filename) == "logging/__init__.py"
                    or "pytest" in filename
                    or "pluggy" in filename
                    or "unittest" in filename
            ):
                return frame

            frame = frame.f_back

        return frame

    # ------------------------------------------------------------------
    # RAW COLOR BLEACHING
    # ------------------------------------------------------------------
    @staticmethod
    def __bleach_non_colored_text(message: str) -> str:
        result: list[str] = []
        plain_buffer: list[str] = []

        i = 0
        n = len(message)
        color_active = False

        def flush_plain():
            if not plain_buffer:
                return  # pragma: no cover
            chunk = "".join(plain_buffer)
            plain_buffer.clear()
            if chunk.strip():
                result.append(CPrint.colorize(chunk, fg=CPrint.FG.CONSOLE_DEFAULT))
            else:
                result.append(chunk)

        while i < n:
            ch = message[i]

            if ch == "\x1b":
                if not color_active:
                    flush_plain()

                start = i
                i += 1
                while i < n and message[i] != "m":
                    i += 1
                i += 1

                seq = message[start:i]
                result.append(seq)

                if seq.endswith("[0m"):
                    color_active = False
                else:
                    color_active = True
            else:
                if color_active:
                    result.append(ch)
                else:
                    plain_buffer.append(ch)
                i += 1

        if not color_active:
            flush_plain()

        return "".join(result)

    # ------------------------------------------------------------------
    # PUBLIC: LEVEL & NAME
    # ------------------------------------------------------------------
    @property
    def name(self) -> str:
        return self._name

    @property
    def level(self) -> int:
        return self._py_logger.level

    @level.setter
    def level(self, value) -> None:
        self._py_logger.setLevel(value)

    # ------------------------------------------------------------------
    # PUBLIC: HANDLER MANAGEMENT
    # ------------------------------------------------------------------
    @staticmethod
    def __normalize_output_mode(mode: str | OutputMode) -> OutputMode:
        if isinstance(mode, OutputMode):
            return mode
        try:
            return OutputMode(mode.lower())
        except ValueError:
            raise ValueError(f"Invalid output_mode: {mode!r}")

    def add_console(
            self,
            level: int = TRACE,
            log_record_details: Optional[LogRecordDetails] = None,
            output_mode: str | OutputMode = OutputMode.COLOR,
    ) -> None:
        if self._retired:
            raise RuntimeError(f"AsyncSmartLogger {self._name!r} has been retired and cannot accept handlers.")

        # 🔹 NEW: avoid adding duplicate console handlers
        for h in self._py_logger.handlers:
            if isinstance(h, logging.StreamHandler) and not hasattr(h, "baseFilename"):
                # console handler already attached
                return  # pragma: no cover

        mode = self.__normalize_output_mode(output_mode)

        if log_record_details is None:
            log_record_details = LogRecordDetails()

        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setLevel(level)

        if mode is OutputMode.JSON:
            formatter = StructuredJSONFormatter(log_record_details, indent=4)
        elif mode is OutputMode.NDJSON:
            formatter = StructuredNDJSONFormatter(log_record_details)
        elif mode is OutputMode.COLOR:
            formatter = StructuredColorFormatter(log_record_details)
        else:
            formatter = StructuredPlainFormatter(log_record_details)

        handler.setFormatter(formatter)
        self._py_logger.addHandler(handler)

        level_name = logging.getLevelName(level)
        self._handlers.append(
            HandlerMetadata(
                kind="console",
                level=logging.getLevelName(level),
                formatter=str(mode.value)
            )
        )
        self._real_handlers.append(handler)

    def remove_console(self) -> None:
        to_remove = [
            h for h in self._py_logger.handlers
            if isinstance(h, logging.StreamHandler)
            and not hasattr(h, "baseFilename")
        ]

        for h in to_remove:
            self._py_logger.removeHandler(h)
            h.close()

    def add_file(
            self,
            log_dir: str,
            logfile_name: str,
            level: Optional[int] = None,
            log_record_details: Optional[LogRecordDetails] = None,
            rotation_logic: Optional[RotationLogic] = None,
            do_not_sanitize_colors_from_string: bool = False,
            output_mode: str | OutputMode = OutputMode.PLAIN,
    ) -> None:
        if self._retired:
            raise RuntimeError(f"AsyncSmartLogger {self._name!r} has been retired and cannot accept handlers.")

        mode = self.__normalize_output_mode(output_mode)

        normalized = os.path.abspath(os.path.normpath(log_dir))
        if log_dir != normalized:   # pragma: no cover
            text = f"for avoiding human errors, log_dir must be normalized. "\
                   f"Got '{log_dir}', where normalized log_dir is '{normalized}'."
            raise ValueError(text)

        os.makedirs(normalized, exist_ok=True)
        log_dir_path = Path(normalized).resolve()
        os.makedirs(log_dir_path, exist_ok=True)

        file_path = log_dir_path / logfile_name
        resolved_path = str(file_path.resolve())

        if log_record_details is None:
            log_record_details = LogRecordDetails()

        # Formatter selection
        if mode is OutputMode.JSON:
            formatter = StructuredJSONFormatter(log_record_details, indent=None)
        elif mode is OutputMode.NDJSON:
            formatter = StructuredNDJSONFormatter(log_record_details)
        else:
            if do_not_sanitize_colors_from_string:
                formatter = PassthroughFormatter()
            else:
                formatter = StructuredPlainFormatter(log_record_details)

        # Handler creation
        if rotation_logic:
            handler = Async_TimedSizedRotatingFileHandler(
                baseFilename=str(file_path),
                rotation_logic=rotation_logic,
            )
        else:
            handler = logging.FileHandler(str(file_path), encoding="utf-8")

        handler.setLevel(level or self._py_logger.level)
        handler.setFormatter(formatter)

        setattr(handler, "do_not_sanitize_colors_from_string", do_not_sanitize_colors_from_string)

        if isinstance(handler, Async_TimedSizedRotatingFileHandler):
            handler.rotation_callback = self.__enqueue_rotation
            handler.resolved_path = resolved_path

        self._py_logger.addHandler(handler)

        level_name = logging.getLevelName(level or self._py_logger.level)
        rotation_meta = None
        if rotation_logic:
            rotation_meta = {
                "maxBytes": rotation_logic.maxBytes,
                "when": rotation_logic.when.name if rotation_logic.when else None,
                "interval": rotation_logic.interval,
                "backupCount": rotation_logic.backupCount,
            }

        rotation_meta = (
            {
                "maxBytes": rotation_logic.maxBytes,
                "when": rotation_logic.when.name if rotation_logic.when else None,
                "interval": rotation_logic.interval,
                "backupCount": rotation_logic.backupCount,
            }
            if rotation_logic else None
        )

        self._handlers.append(
            HandlerMetadata(
                kind="file",
                level=logging.getLevelName(level or self._py_logger.level),
                formatter=str(mode.value),
                path=resolved_path,
                rotation=rotation_meta,
                do_not_sanitize_colors_from_string=do_not_sanitize_colors_from_string,
            )
        )

    def remove_file_handler(self, logfile_name: str, log_dir: str) -> None:
        target_path = Path(log_dir) / logfile_name

        to_remove = [
            h for h in self._py_logger.handlers
            if isinstance(h, logging.FileHandler)
            and Path(h.baseFilename) == target_path
        ]

        for h in to_remove:
            h.close()
            self._py_logger.removeHandler(h)

        # Also remove metadata
        self._handlers = [
            h for h in self._handlers
            if not (h.kind == "file" and h.path == str(target_path))
        ]

    @property
    def handler_info(self) -> list[dict[str, Any]]:
        return [asdict(h) for h in self._handlers]

    @property
    def console_handler(self):
        for h in self._py_logger.handlers:
            if isinstance(h, logging.StreamHandler) and not hasattr(h, "baseFilename"):
                return h
        return None

    @property
    def file_handlers(self):
        return [
            h for h in self._py_logger.handlers
            if hasattr(h, "baseFilename")
        ]

    @property
    def output_targets(self) -> list[str]:
        return [
            "console" if h.kind == "console" else h.path
            for h in self._handlers
        ]

    @classmethod
    def audit_handler_info(cls) -> Optional[dict[str, object]]:
        """
        Returns metadata for the active audit handler, if auditing is enabled.
        """
        h = cls.__audit_handler
        if h is None:
            return None

        # Determine formatter mode
        fmt = h.formatter
        if isinstance(fmt, StructuredJSONFormatter):
            formatter = "json"
        elif isinstance(fmt, StructuredNDJSONFormatter):
            formatter = "ndjson"
        elif isinstance(fmt, StructuredColorFormatter):
            formatter = "color"
        else:
            formatter = "plain"

        rotation_meta = None
        rotation_logic = getattr(h, "rotation_logic", None)
        if rotation_logic:
            rotation_meta = {
                "maxBytes": rotation_logic.maxBytes,
                "when": rotation_logic.when.name if rotation_logic.when else None,
                "interval": rotation_logic.interval,
                "backupCount": rotation_logic.backupCount,
            }

        return {
            "kind": "file" if hasattr(h, "baseFilename") else "console",
            "level": logging.getLevelName(h.level),
            "formatter": formatter,
            "path": getattr(h, "baseFilename", None),
            "rotation": rotation_meta,
            "do_not_sanitize_colors_from_string": getattr(h, "do_not_sanitize_colors_from_string", False),
        }


    # ------------------------------------------------------------------
    # INTERNAL: QUEUE ENQUEUE HELPERS
    # ------------------------------------------------------------------
    async def _enqueue_log(
        self,
        level: int,
        msg: str,
        args: tuple[Any, ...],
        extra: dict[str, Any],
        fields: dict[str, Any],
        exc_info: tuple | None,
        stack_info_flag: bool,
        pathname: str,
        lineno: int,
        func_name: str,
    ) -> None:
        if self._stopped:
            raise RuntimeError("AsyncSmartLogger has been shut down.")
        if self._retired:
            raise RuntimeError(f"AsyncSmartLogger {self._name!r} has been retired and cannot be used.")

        queue_item = _QueueItem(
            op=AsyncOp.LOG,
            payload={
                "level": level,
                "msg": msg,
                "args": args,
                "extra": extra,
                "fields": fields,
                "exc_info": exc_info,
                "stack_info_flag": stack_info_flag,
                "pathname": pathname,
                "lineno": lineno,
                "func_name": func_name,
            },
        )

        try:
            self._queue.put_nowait(queue_item)
        except asyncio.QueueFull:
            # cooperative yield, then retry
            await asyncio.sleep(0)
            await self._queue.put(queue_item)

        self._messages_enqueued += 1

        # Coping with Backpressure:
        # auto-flush when queue is too deep
        if self._queue.qsize() > 10000:
            # hand control back to the event loop to give worker a chance to drain
            await asyncio.sleep(0)
            # WARNING: don't use "await self._queue.join()"
            #          that's an actual blocking point that would defeat the purpose of async logging.

    def messages_enqueued(self):
        return self._messages_enqueued

    async def __enqueue_raw(self, message: str, end: str) -> None:
        if self._stopped:
            raise RuntimeError("AsyncSmartLogger has been shut down.")
        if self._retired:
            raise RuntimeError(f"AsyncSmartLogger {self._name!r} has been retired and cannot be used.")

        await self._queue.put(
            _QueueItem(
                op=AsyncOp.RAW,
                payload={"message": message, "end": end},
            )
        )

    def __enqueue_rotation(self, handler):
        if self._stopped or self._retired:
            return  # pragma: no cover

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        item = _QueueItem(op=AsyncOp.ROTATE, payload={"handler": handler})

        if loop is self._loop:
            # Already on the logger's loop (worker context) → enqueue synchronously
            self._queue.put_nowait(item)
        else:
            # Called from another thread / loop → schedule thread-safe
            self._loop.call_soon_threadsafe(self._queue.put_nowait, item)

    # ------------------------------------------------------------------
    # PUBLIC: ASYNC LOGGING API
    # ------------------------------------------------------------------
    async def a_log(self, level: int, msg: str, *args, **kwargs) -> None:
        if self._retired:
            raise RuntimeError(f"AsyncSmartLogger {self._name!r} has been retired and cannot be used.")

        if not self._py_logger.isEnabledFor(level):
            return  # pragma: no cover

        exc_info_flag = kwargs.pop("exc_info", False)
        stack_info_flag = kwargs.pop("stack_info", False)

        captured_exc = sys.exc_info() if exc_info_flag else None

        extra = kwargs.pop("extra", {}) or {}
        fields = kwargs

        # 🔹 capture caller BEFORE any await
        frame = inspect.currentframe().f_back  # caller of a_log (a_info / a_warning / etc.)
        while frame:
            filename = frame.f_code.co_filename.replace("\\", "/")
            if "async_smartlogger.py" not in filename:
                break
            frame = frame.f_back

        if frame is not None:
            pathname = frame.f_code.co_filename
            lineno = frame.f_lineno
            func_name = frame.f_code.co_name
        else:
            # very defensive fallback
            pathname = "<unknown>"
            lineno = 0
            func_name = "<unknown>"

        await self._enqueue_log(
            level,
            msg,
            args,
            extra,
            fields,
            exc_info=captured_exc,
            stack_info_flag=stack_info_flag,
            pathname=pathname,
            lineno=lineno,
            func_name=func_name,
        )

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
        if self._retired:
            raise RuntimeError(f"AsyncSmartLogger {self._name!r} has been retired and cannot be used.")
        await self.__enqueue_raw(message, end)

    # ------------------------------------------------------------------
    # DYNAMIC LEVEL SUPPORT
    # ------------------------------------------------------------------
    @staticmethod
    def levels() -> dict[str, int]:
        levels = {"NOTSET": logging.NOTSET}
        for name, meta in LEVELS.all().items():
            levels[name] = meta["value"]
        return levels

    @staticmethod
    def __safeguard_internals(name: str, value: int) -> None:
        if name in AsyncSmartLogger.__dict__:
            raise ValueError(f"Cannot override internal AsyncSmartLogger attribute '{name}'")

        if name in LEVELS.all():
            raise ValueError(f"Level '{name}' already exists")  # pragma: no cover

        for meta in LEVELS.all().values():
            if meta["value"] == value:
                raise ValueError(f"Level value '{value}' already exists")

        if value < 0:
            raise ValueError("Negative level values are reserved for internal operations")  # pragma: no cover

    @staticmethod
    def register_level(name: str, value: int, style: Optional[LevelStyle] = None) -> None:
        AsyncSmartLogger.__safeguard_internals(name, value)
        LEVELS.register(name, value, style)

    def __getattr__(self, item: str) -> Any:
        if item.startswith("a_"):
            level_name = item[2:].upper()
            meta = LEVELS.all().get(level_name)
            if meta is not None:
                level_value = meta["value"]

                async def dynamic_level_method(msg: str, *args: Any, **kwargs: Any) -> None:
                    await self.a_log(level_value, msg, *args, **kwargs)

                setattr(self, item, dynamic_level_method)
                return dynamic_level_method

        raise AttributeError(f"{type(self).__name__!s} object has no attribute {item!r}")

    # ------------------------------------------------------------------
    # COLOR THEMES
    # ------------------------------------------------------------------
    @staticmethod
    def apply_color_theme(theme: dict[int, LevelStyle]) -> None:
        if theme is None:
            for name, meta in LEVELS.all().items():
                meta["style"] = meta["default_style"]
            return  # pragma: no cover

        if not isinstance(theme, dict):
            raise TypeError("Theme must be a dict mapping level numbers to LevelStyle instances")

        for level, style in theme.items():
            if not isinstance(level, int):
                raise TypeError(f"Theme key '{level}' must be an int (log level number)")
            if not isinstance(style, LevelStyle):
                raise TypeError(f"Theme value for level {level} must be a LevelStyle instance")

        for level_name, meta in LEVELS.all().items():
            value = meta["value"]

            if value not in theme:
                continue    # pragma: no cover

            style = theme[value]

            if not isinstance(style, LevelStyle):
                raise TypeError(
                    f"Theme entry for level {value} must be a LevelStyle, "
                    f"got {type(style).__name__}"
                )

            meta["style"] = style

    # ------------------------------------------------------------------
    # FLUSH & SHUTDOWN
    # ------------------------------------------------------------------
    async def flush(self) -> None:
        """
        Wait until all queued work (LOG, RAW, ROTATE) is done,
        then flush all underlying handlers.
        """
        # 1. Drain the async pipeline completely
        await self._queue.join()

        # 2. Flush all handlers' streams
        for handler in self._py_logger.handlers:
            flush = getattr(handler, "flush", None)
            if callable(flush):
                flush()

    async def shutdown(self):
        if self._stopped:
            return

        self._stopped = True

        # 1. Drain queue
        await self._queue.join()

        # 2. Stop workers
        for task in self._worker_tasks:
            self._queue.put_nowait(_QueueItem(op=AsyncOp.SENTINEL, payload={}))
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)

        # 3. Flush + close handlers
        for handler in self._py_logger.handlers:
            # noinspection PyBroadException
            try:
                handler.flush()
            except Exception:   # pragma: no cover
                pass
            # noinspection PyBroadException
            try:
                handler.close()
            except Exception:   # pragma: no cover
                pass

        self._py_logger.handlers.clear()

    # ------------------------------------------------------------------
    # AUDITING (class-level)
    # ------------------------------------------------------------------
    @classmethod
    async def audit_everything(
        cls,
        *,
        log_dir: str,
        logfile_name: str,
        rotation_logic: Optional[RotationLogic] = None,
        details: Optional[LogRecordDetails] = None,
    ) -> None:
        if cls.__audit_enabled:
            return  # pragma: no cover

        cls.__audit_enabled = True

        audit_logger = AsyncSmartLogger("_async_audit", cls.__default_level)
        cls.__audit_logger = audit_logger

        if details is None:
            details = LogRecordDetails()

        formatter = AuditFormatter(details)

        audit_logger.add_file(
            log_dir=log_dir,
            logfile_name=logfile_name,
            rotation_logic=rotation_logic,
            output_mode=OutputMode.PLAIN,
        )

        # Override the formatter on the actual handler
        handler = audit_logger._py_logger.handlers[-1]
        handler.setFormatter(formatter)

        cls.__audit_handler = audit_logger._py_logger.handlers[-1]

    @classmethod
    async def terminate_auditing(cls) -> None:
        if not cls.__audit_enabled:
            return  # pragma: no cover

        cls.__audit_enabled = False

        if cls.__audit_logger and cls.__audit_handler:
            # noinspection PyBroadException
            try:
                cls.__audit_logger._py_logger.removeHandler(cls.__audit_handler)
            except Exception:   # pragma: no cover
                pass    # pragma: no cover

        cls.__audit_logger = None
        cls.__audit_handler = None

    # ------------------------------------------------------------------
    # METADATA SNAPSHOT
    # ------------------------------------------------------------------
    @classmethod
    def get_record(cls, *, exc_info: bool = False, stack_info: bool = False) -> RetrievedRecord:
        now = datetime.now()

        # Caller frame
        frame = inspect.stack()[1]
        frame_info = frame.frame
        file_path = frame_info.f_code.co_filename
        file_name = os.path.basename(file_path)
        lineno = frame_info.f_lineno
        func_name = frame_info.f_code.co_name

        # Thread / task / process
        thread = threading.current_thread()
        task = asyncio.current_task()

        # Exception metadata (only inside except block)
        exc = None
        if exc_info:
            exc_type, exc_val, tb = sys.exc_info()
            if exc_type:
                exc = {
                    "type": exc_type.__name__,
                    "message": str(exc_val),
                    "traceback": traceback.format_exception(exc_type, exc_val, tb),
                }

        # Stack metadata
        stack = None
        if stack_info:
            stack = "".join(traceback.format_stack())

        return RetrievedRecord(
            timestamp=now.isoformat(),
            relative_created=time.monotonic(),
            file_path=file_path,
            file_name=file_name,
            lineno=lineno,
            func_name=func_name,
            thread_id=thread.ident,
            thread_name=thread.name,
            task_name=(task.get_name() if task else None),
            process_id=os.getpid(),
            process_name=multiprocessing.current_process().name,
            exc_info=exc,
            stack_info=stack,
        )

    # ------------------------------------------------------------------
    # retire & destroy
    # ------------------------------------------------------------------
    def retire(self) -> None:
        self._retired = True

    def destroy(self) -> None:
        for handler in list(self._real_handlers):
            # noinspection PyBroadException
            try:
                self._py_logger.removeHandler(handler)
            except Exception:   # pragma: no cover
                pass    # pragma: no cover
            # noinspection PyBroadException
            try:
                handler.close()
            except Exception:   # pragma: no cover
                pass    # pragma: no cover

        self._real_handlers.clear()
        self._handlers.clear()
        self._retired = True


# ======================================================================
#  Global stdout logger (lazy initialization)
# ======================================================================

__async_stdout_logger = None
__async_stdout_lock = threading.Lock()


def __get_async_stdout_logger() -> AsyncSmartLogger:
    global __async_stdout_logger

    if __async_stdout_logger is not None:
        return __async_stdout_logger

    with __async_stdout_lock:
        if __async_stdout_logger is None:
            lg = AsyncSmartLogger("_async_stdout", level=logging.INFO)
            lg.add_console(level=logging.INFO)
            lg._py_logger.propagate = False
            __async_stdout_logger = lg

    return __async_stdout_logger


async def a_stdout(*args, sep=" ", end="\n"):
    """
    An AsyncSmartLogger‑synchronized replacement for print().

    Behaves exactly like print(), including handling of sep and end,
    but routes output through AsyncSmartLogger.raw() so console output is
    perfectly synchronized with all AsyncSmartLogger log messages.

    Auto-flushes to guarantee ordering with async log messages.
    """
    lg = __get_async_stdout_logger()

    # Capture print() output exactly as Python formats it
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        print(*args, sep=sep, end=end)

    text = buffer.getvalue()

    # Enqueue RAW write
    await lg.a_raw(text, end="")

    # Force synchronization with all async log messages
    await lg.flush()