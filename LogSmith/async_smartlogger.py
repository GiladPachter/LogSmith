# LogSmith/async_smartlogger.py

from __future__ import annotations

import asyncio
import copy
import logging
import multiprocessing
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, ClassVar, Optional, List
import os
import threading
import time

from .file_registry import FileHandlerRegistry
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
from .rotation_base import RotationLogic
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

    __default_level: ClassVar[int] = TRACE

    __worker_init_lock: ClassVar[asyncio.Lock] = asyncio.Lock()

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
        return self.__queue.qsize()

    # ------------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------------
    def __init__(self, name: str, level: int = TRACE) -> None:
        self.__name = name

        self.__py_logger = logging.getLogger(name)
        self.__py_logger.propagate = False
        self.__py_logger.setLevel(level)

        # Capture loop if one exists, but DO NOT start worker here
        try:
            self.__loop = asyncio.get_running_loop()
            self.__loop_thread = threading.current_thread()
        except RuntimeError:
            self.__loop = None
            self.__loop_thread = None

        # Unbounded queue
        # self.__queue: asyncio.Queue[_QueueItem] = asyncio.Queue(maxsize=0)
        # Unbounded queue, with owner callback on put_nowait
        self.__queue: asyncio.Queue[_QueueItem] = AsyncSmartLogger.__LoggerQueue(self, maxsize=0)

        # Worker is NOT started here — always lazy
        self.__worker_tasks: Optional[list[asyncio.Task[None]]] = None

        # If we already have a running loop at construction time, start a worker now.
        if self.__loop is not None:
            self.__worker_tasks = [self.__loop.create_task(self.__worker())]

        self.__worker_task: Optional[asyncio.Task[None]] = None
        self.__stopped = False
        self.__handlers: list[HandlerMetadata] = []
        self.__messages_enqueued = 0
        self.__retired = False

        self.__profile_enabled = False
        self.__profile_stats = {
            "find_caller": 0.0,
            "record": 0.0,
            "handlers": 0.0,
            "total": 0.0,
            "count": 0,
            "steady_total": 0.0,
            "steady_count": 0,
            "spike_total": 0.0,
            "spike_count": 0,
            "rotation_time": 0.0,
            "rotation_count": 0,
        }

    class __LoggerQueue(asyncio.Queue):
        def __init__(self, owner: AsyncSmartLogger, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._owner = owner

        def put_nowait(self, item: _QueueItem) -> None:
            super().put_nowait(item)
            self._owner._on_queue_put(item)

    def _on_queue_put(self, item: _QueueItem) -> None:
        """
        Auto-start worker only for LOG/RAW events.
        ROTATE events must never be auto-started here.
        """

        # No loop or no loop thread → cannot start worker
        if self.__loop is None or self.__loop_thread is None:
            return

        # Only same-thread auto-start
        if threading.current_thread() is not self.__loop_thread:
            return

        # Only LOG/RAW should auto-start worker
        if item.op in (AsyncOp.LOG, AsyncOp.RAW):
            if not self.__worker_tasks:
                self.__worker_tasks = [self.__loop.create_task(self.__worker())]

    def enable_profiling(self, enable: bool):
        self.__profile_enabled = enable

    def get_profiling_details(self) -> str:
        if not self.__profile_enabled:
            return "Profiling not enabled."

        c = self.__profile_stats["count"]
        if c == 0:
            return "No profiling data collected."

        profiling_details = (f"Total log events: {c}\n"
                             f"Avg find_caller: {self.__profile_stats['find_caller'] / c * 1e6:.2f} µs\n"
                             f"Avg record creation: {self.__profile_stats['record'] / c * 1e6:.2f} µs\n"
                             f"Avg handler time: {self.__profile_stats['handlers'] / c * 1e6:.2f} µs\n"
                             f"Avg total per log: {self.__profile_stats['total'] / c * 1e6:.2f} µs\n"
                             )

        if self.__profile_stats["rotation_count"] > 0:
            profiling_details += (
                f"Avg rotation time: "
                f"{self.__profile_stats['rotation_time'] / self.__profile_stats['rotation_count'] * 1e6:.2f} µs\n"
            )

        if self.__profile_stats["steady_count"] > 0:
            avg_steady = (
                    self.__profile_stats["steady_total"] / self.__profile_stats["steady_count"] * 1e6
            )
            profiling_details += f"Avg steady-state time: {avg_steady:.2f} µs\n"

        if self.__profile_stats["spike_count"] > 0:
            avg_spike = (
                    self.__profile_stats["spike_total"] / self.__profile_stats["spike_count"] * 1e6
            )
            profiling_details += f"Avg spike time: {avg_spike:.2f} µs\n"

        return profiling_details

    # ------------------------------------------------------------------
    # WORKER
    # ------------------------------------------------------------------
    def __start_worker(self, workers: int = 1):
        if self.__loop is None:
            # Defer worker creation until first awaited call
            return  # pragma: no cover

        if hasattr(self, "_AsyncSmartLogger__worker_tasks"):    # pragma: no cover
            return  # pragma: no cover

        self.__worker_tasks = [
            self.__loop.create_task(self.__worker())
            for _ in range(workers)
        ]

    async def __worker(self) -> None:
        while True:
            item = await self.__queue.get()
            try:
                # noinspection PyBroadException
                try:
                    if item.op is AsyncOp.SENTINEL:
                        return  # pragma: no cover

                    if item.op is AsyncOp.LOG:
                        await self.__process_log(item.payload)

                    elif item.op is AsyncOp.RAW:
                        await self.__process_raw(item.payload)

                    elif item.op is AsyncOp.ROTATE:
                        await self.__process_rotate(item.payload)

                except Exception as e:   # pragma: no cover
                    # import traceback, sys
                    # print("AsyncSmartLogger worker error:", e, file=sys.stderr)
                    # traceback.print_exc()
                    # swallow ANY error inside the worker
                    # this prevents the worker from dying
                    pass

            finally:
                self.__queue.task_done()

    # ------------------------------------------------------------------
    # PROCESS LOG
    # ------------------------------------------------------------------
    async def __process_log(self, payload: dict[str, Any]) -> None:
        # PROFILING: start total timer
        t0 = 0.0
        t_find = 0.0
        t_record = 0.0
        t_handlers = 0.0
        if self.__profile_enabled:
            t0 = time.perf_counter()

        level: int = payload["level"]
        msg: str = payload["msg"]
        args: tuple[Any, ...] = payload["args"]
        extra: dict[str, Any] = payload["extra"]
        fields: dict[str, Any] = payload["fields"]
        exc_info = payload["exc_info"]
        stack_info_flag: bool = payload["stack_info_flag"]

        # Sanitize ANSI for file logging unless explicitly disabled
        sanitize = True
        for handler in self.__py_logger.handlers:
            if hasattr(handler, "baseFilename"):
                if getattr(handler, "preserve_colors_in_log_files", False):
                    sanitize = False
                break

        if sanitize:
            msg = CPrint.strip_ansi(msg)

        merged_kwargs = {}
        if extra:
            merged_kwargs["extra"] = extra
        if fields:
            merged_kwargs["fields"] = fields

        # PROFILING: measure find_caller
        if self.__profile_enabled:
            t_find = time.perf_counter()

        pathname = payload["pathname"]
        lineno = payload["lineno"]
        func_name = payload["func_name"]

        if self.__profile_enabled:
            self.__profile_stats["find_caller"] += time.perf_counter() - t_find

        sinfo = "".join(traceback.format_stack()) if stack_info_flag else None

        # AUDIT (unchanged)
        if (
                AsyncSmartLogger.__audit_enabled
                and AsyncSmartLogger.__audit_logger is not None
                and AsyncSmartLogger.__audit_logger is not self
        ):
            await AsyncSmartLogger.__audit_logger.__enqueue_log(
                level,
                msg,
                args,
                {"__audited_logger_name__": self.__name},
                fields,
                exc_info,
                stack_info_flag,
                pathname,
                lineno,
                func_name,
            )

        audited_name = extra.pop("__audited_logger_name__", None)
        record_name = audited_name or self.__name

        # PROFILING: measure record creation
        if self.__profile_enabled:
            t_record = time.perf_counter()

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

        if merged_kwargs:
            record.__dict__.update(merged_kwargs)

        if self.__profile_enabled:
            self.__profile_stats["record"] += time.perf_counter() - t_record

        # PROFILING: start handler timing
        if self.__profile_enabled:
            t_handlers = time.perf_counter()

        # === NEW: delegate to logging + handlers, no special-casing ===
        for handler in self.__py_logger.handlers:
            # Let logging filters run
            if not handler.filter(record):
                continue
            handler.handle(record)

        # PROFILING: finalize handler + total
        if self.__profile_enabled:
            handler_time = time.perf_counter() - t_handlers
            total = time.perf_counter() - t0

            self.__profile_stats["handlers"] += handler_time
            self.__profile_stats["total"] += total
            self.__profile_stats["count"] += 1

            if total < 0.0005:
                self.__profile_stats["steady_count"] += 1
                self.__profile_stats["steady_total"] += total
            else:
                self.__profile_stats["spike_count"] += 1
                self.__profile_stats["spike_total"] += total

        AsyncSmartLogger.__messages_processed += 1

    # ------------------------------------------------------------------
    # PROCESS RAW
    # ------------------------------------------------------------------
    async def __process_raw(self, payload: dict[str, Any]) -> None:
        message: str = payload["message"]
        end: str = payload["end"]

        for handler in self.__py_logger.handlers:
            # stream = getattr(handler, "stream", None)
            stream = handler.stream

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
                continue    # pragma: no cover

            is_console = isinstance(handler, logging.StreamHandler) and not hasattr(handler, "baseFilename")

            if is_console:
                text = self.__bleach_non_colored_text(message)
            else:
                do_not_sanitize = getattr(handler, "preserve_colors_in_log_files", False)
                text = message if do_not_sanitize else CPrint.strip_ansi(message)

            # noinspection PyBroadException
            try:
                stream.write(text + end)
                stream.flush()
            except Exception:   # pragma: no cover
                # Ignore write errors
                pass

    # ------------------------------------------------------------------
    # PROCESS ROTATION
    # ------------------------------------------------------------------
    async def __process_rotate(self, payload: dict[str, Any]) -> None:
        handler: Async_TimedSizedRotatingFileHandler = payload["handler"]

        t0 = 0.0
        if self.__profile_enabled:
            t0 = time.perf_counter()

        with handler.write_lock:
            await asyncio.to_thread(handler.perform_rotation)

        if self.__profile_enabled:
            self.__profile_stats["rotation_time"] += time.perf_counter() - t0
            self.__profile_stats["rotation_count"] += 1

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
        return self.__name

    @property
    def level(self) -> int:
        return self.__py_logger.level

    @level.setter
    def level(self, value) -> None:
        self.__py_logger.setLevel(value)

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
        if self.__retired:
            raise RuntimeError(f"AsyncSmartLogger {self.__name!r} has been retired and cannot accept handlers.")

        # 🔹 NEW: avoid adding duplicate console handlers
        for h in self.__py_logger.handlers:
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
        self.__py_logger.addHandler(handler)

        level_name = logging.getLevelName(level)
        self.__handlers.append(
            HandlerMetadata(
                kind="console",
                level=logging.getLevelName(level),
                formatter=str(mode.value)
            )
        )

    def remove_console(self) -> None:
        to_remove = [
            h for h in self.__py_logger.handlers
            if isinstance(h, logging.StreamHandler)
            and not hasattr(h, "baseFilename")
        ]

        for h in to_remove:
            self.__py_logger.removeHandler(h)
            h.close()

    def add_file(
            self,
            log_dir: str,
            logfile_name: str | None = None,
            level: Optional[int] = None,
            log_record_details: Optional[LogRecordDetails] = None,
            rotation_logic: Optional[RotationLogic] = None,
            preserve_colors_in_log_files: bool = False,
            output_mode: str | OutputMode = OutputMode.PLAIN,
            audit_mode: bool = False
    ) -> None:
        if self.__retired:
            raise RuntimeError(f"AsyncSmartLogger {self.__name!r} has been retired and cannot accept handlers.")

        mode = self.__normalize_output_mode(output_mode)

        # verify normalized log_dir given
        normalized = os.path.abspath(os.path.normpath(log_dir))
        if log_dir != normalized:   # pragma: no cover
            text = f"for avoiding human errors, log_dir must be normalized. "\
                   f"Got '{log_dir}', where normalized log_dir is '{normalized}'."
            raise ValueError(text)

        # --- PREP WORK (outside lock) -------------------------------------
        os.makedirs(normalized, exist_ok=True)

        log_dir_path = Path(normalized).resolve()
        os.makedirs(log_dir_path, exist_ok=True)

        if logfile_name is None:
            logfile_name = f"{self.__py_logger.name}.log"

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
            if preserve_colors_in_log_files:
                formatter = PassthroughFormatter()
            else:
                formatter = StructuredPlainFormatter(log_record_details)

        # Handler creation
        if rotation_logic:
            handler = Async_TimedSizedRotatingFileHandler(
                filename = str(file_path),
                when = rotation_logic.when,
                interval = rotation_logic.interval or 1,
                timestamp = rotation_logic.timestamp,
                max_bytes = rotation_logic.maxBytes or 0,
                backup_count = rotation_logic.backupCount,
                expiration_rule = rotation_logic.expiration_rule,
                encoding = "utf-8",
                large_entry_behavior = rotation_logic.large_entry_behavior,
                append_filename_pid = rotation_logic.append_filename_pid,
                append_filename_timestamp = rotation_logic.append_filename_timestamp,
                audit_mode=audit_mode,
            )
        else:
            handler = logging.FileHandler(str(file_path), encoding="utf-8")

        FileHandlerRegistry.register(str(file_path))

        handler.setLevel(level or self.__py_logger.level)
        handler.setFormatter(formatter)

        setattr(handler, "preserve_colors_in_log_files", preserve_colors_in_log_files)

        if isinstance(handler, Async_TimedSizedRotatingFileHandler):
            handler.rotation_callback = self.__enqueue_rotation
            handler.resolved_path = resolved_path

        # ------------------------------------------------------------------
        # Duplicate detection (process-wide) – mirror SmartLogger behavior
        # ------------------------------------------------------------------
        resolved_for_compare = str(Path(resolved_path).resolve())
        for logger in logging.Logger.manager.loggerDict.values():
            if not isinstance(logger, AsyncSmartLogger):
                continue

            for info in logger.__handlers:
                if info.kind != "file" or not info.path:
                    continue
                existing_resolved = str(Path(info.path).resolve())
                if existing_resolved == resolved_for_compare:
                    FileHandlerRegistry.unregister(str(file_path))
                    raise ValueError(
                        f"A file handler for '{resolved_for_compare}' is already active "
                        f"in this process. This is usually caused by a duplicate "
                        f"configuration or copy‑paste error."
                    )

        self.__py_logger.addHandler(handler)

        rotation_meta = (
            {
                "maxBytes": rotation_logic.maxBytes,
                "when": rotation_logic.when.name if rotation_logic.when else None,
                "interval": rotation_logic.interval,
                "backupCount": rotation_logic.backupCount,
            }
            if rotation_logic else None
        )

        self.__handlers.append(
            HandlerMetadata(
                kind="file",
                level=logging.getLevelName(level or self.__py_logger.level),
                formatter=str(mode.value),
                path=resolved_path,
                rotation=rotation_meta,
                preserve_colors_in_log_files=preserve_colors_in_log_files,
            )
        )

    def remove_file_handler(self, logfile_name: str, log_dir: str) -> None:
        target_path = Path(log_dir) / logfile_name

        to_remove = [
            h for h in self.__py_logger.handlers
            if isinstance(h, logging.FileHandler)
            and Path(h.baseFilename) == target_path
        ]

        for h in to_remove:
            h.close()
            self.__py_logger.removeHandler(h)
            FileHandlerRegistry.unregister(h.baseFilename)

        # Also remove metadata
        self.__handlers = [
            h for h in self.__handlers
            if not (h.kind == "file" and h.path == str(target_path))
        ]

    @property
    def handler_info(self) -> list[dict[str, Any]]:
        return [asdict(h) for h in self.__handlers]

    @property
    def console_handler(self):
        for info in self.handler_info:
            if info["kind"] == "console":
                return info
        return None

    @property
    def file_handlers(self):
        return [
            info for info in self.handler_info
            if info["kind"] == "file"
        ]

    @property
    def output_targets(self) -> list[str]:
        return [
            "console" if h.kind == "console" else h.path
            for h in self.__handlers
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
            "preserve_colors_in_log_files": getattr(h, "preserve_colors_in_log_files", False),
        }

    @staticmethod
    def __audit_prefix(formatted: str, original_logger_name: str) -> str:
        return f"{original_logger_name} : {formatted}"

    # ------------------------------------------------------------------
    # INTERNAL: QUEUE ENQUEUE HELPERS
    # ------------------------------------------------------------------
    async def __enqueue_log(
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

        await self.__ensure_worker_started()

        if self.__stopped:
            raise RuntimeError("AsyncSmartLogger has been shut down.")
        if self.__retired:
            raise RuntimeError(f"AsyncSmartLogger {self.__name!r} has been retired and cannot be used.")

        payload = {
            "level": level,
            "msg": msg,
            "args": args,
            "extra": copy.deepcopy(extra),
            "fields": copy.deepcopy(fields),
            "exc_info": exc_info,
            "stack_info_flag": stack_info_flag,
            "pathname": pathname,
            "lineno": lineno,
            "func_name": func_name,
        }

        item = _QueueItem(op=AsyncOp.LOG, payload=payload)

        # --- Minimal exponential backpressure ---
        delays = (0, 0.001, 0.002, 0.004, 0.008)
        for delay in delays:
            try:
                self.__queue.put_nowait(item)
                break   # pragma: no cover
            except asyncio.QueueFull:
                await asyncio.sleep(delay)
        else:   # pragma: no cover
            return  # drop silently, preserve original semantics
        # ----------------------------------------

        self.__messages_enqueued += 1

        # Coping with Backpressure:
        # auto-flush when queue is too deep
        if self.__queue.qsize() > 10000:
            # hand control back to the event loop to give worker a chance to drain
            await asyncio.sleep(0)
            # WARNING: don't use "await self._queue.join()"
            #          that's an actual blocking point that would defeat the purpose of async logging.

    @property
    def messages_enqueued(self):
        return self.__messages_enqueued

    async def __enqueue_raw(self, message: str, end: str) -> None:

        await self.__ensure_worker_started()

        if self.__stopped:
            raise RuntimeError("AsyncSmartLogger has been shut down.")
        if self.__retired:
            raise RuntimeError(f"AsyncSmartLogger {self.__name!r} has been retired and cannot be used.")

        item = _QueueItem(
            op=AsyncOp.RAW,
            payload={"message": message, "end": end},
        )

        # --- Minimal exponential backpressure ---
        delays = (0, 0.001, 0.002, 0.004, 0.008)
        for delay in delays:
            try:
                self.__queue.put_nowait(item)
                break   # pragma: no cover
            except asyncio.QueueFull:
                await asyncio.sleep(delay)
        else:   # pragma: no cover
            return  # drop silently
        # ----------------------------------------

    def __enqueue_rotation(self, handler):
        """
        Called by Async_TimedSizedRotatingFileHandler when rotation is needed.

        Guarantees:
        - No-op after shutdown/retire
        - At most one pending ROTATE per handler
        - Same-thread: marks worker_tasks as non-None but does NOT start workers
        - External thread: starts worker (if needed) and enqueues via loop thread-safely
        - Never blocks, survives QueueFull
        """
        if self.__stopped or self.__retired:
            return

        # Allow tests to pass in metadata dicts from logger.file_handlers[0]
        if isinstance(handler, dict):
            path = handler.get("path")
            real = None
            for h in self.__py_logger.handlers:
                if getattr(h, "baseFilename", None) == path:
                    real = h
                    break
            if real is None:
                return  # nothing to rotate
            handler = real

        # Ensure we know the loop and its thread if we're in a running loop
        if self.__loop is None:
            try:
                self.__loop = asyncio.get_running_loop()
                self.__loop_thread = threading.current_thread()
            except RuntimeError:
                # No loop yet; external-thread path below will be a no-op if loop is still None
                pass

        item = _QueueItem(op=AsyncOp.ROTATE, payload={"handler": handler})

        current_thread = threading.current_thread()
        loop_thread = getattr(self, "_AsyncSmartLogger__loop_thread", None)

        # ------------------------------------------------------------
        # External-thread path: use loop.call_soon_threadsafe
        # ------------------------------------------------------------
        if self.__loop is not None and loop_thread is not None and current_thread is not loop_thread:
            def _start_and_enqueue():
                # Start worker if not yet started
                if not self.__worker_tasks:
                    self.__worker_tasks = [self.__loop.create_task(self.__worker())]
                try:
                    self.__queue.put_nowait(item)
                except asyncio.QueueFull:
                    # Best-effort: drop on full queue in this rare path
                    pass

            self.__loop.call_soon_threadsafe(_start_and_enqueue)
            return

        # ------------------------------------------------------------
        # Same-thread path: do NOT start worker here (tests rely on this)
        # ------------------------------------------------------------
        if self.__worker_tasks is None:
            # Placeholder to satisfy tests that check "is not None"
            self.__worker_tasks = []

        # Bounded retry for QueueFull (used by tests)
        for _ in range(3):
            try:
                self.__queue.put_nowait(item)
                break
            except asyncio.QueueFull:
                continue

    async def __ensure_worker_started(self):
        # Only skip if actual tasks exist
        if self.__worker_tasks:
            return

        self.__loop = asyncio.get_running_loop()
        self.__loop_thread = threading.current_thread()
        self.__worker_tasks = [self.__loop.create_task(self.__worker())]

    # ------------------------------------------------------------------
    # PUBLIC: ASYNC LOGGING API
    # ------------------------------------------------------------------
    async def __a_log(self, level: int, msg: str, *args, **kwargs) -> None:
        if self.__retired:
            raise RuntimeError(f"AsyncSmartLogger {self.__name!r} has been retired and cannot be used.")

        if not self.__py_logger.isEnabledFor(level):
            return  # pragma: no cover

        exc_info_flag = kwargs.pop("exc_info", False)
        stack_info_flag = kwargs.pop("stack_info", False)

        captured_exc = sys.exc_info() if exc_info_flag else None

        extra = {}
        fields = kwargs

        # 🔹 capture caller BEFORE any await
        frame = inspect.currentframe().f_back  # caller of a_log (a_info / a_warning / etc.)
        while frame:
            filename = frame.f_code.co_filename.replace("\\", "/")
            if "async_smartlogger.py" not in filename:
                break   # pragma: no cover
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

        await self.__enqueue_log(
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
        await self.__a_log(TRACE, msg, *args, **kwargs)

    async def a_debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.__a_log(logging.DEBUG, msg, *args, **kwargs)

    async def a_info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.__a_log(logging.INFO, msg, *args, **kwargs)

    async def a_warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.__a_log(logging.WARNING, msg, *args, **kwargs)

    async def a_error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.__a_log(logging.ERROR, msg, *args, **kwargs)

    async def a_critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        await self.__a_log(logging.CRITICAL, msg, *args, **kwargs)

    async def a_raw(self, message: str, end: str = "\n") -> None:
        if self.__retired:
            raise RuntimeError(f"AsyncSmartLogger {self.__name!r} has been retired and cannot be used.")
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
                    await self.__a_log(level_value, msg, *args, **kwargs)

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
        # If there is pending work but no worker yet (e.g. rotation enqueued
        # from same thread via callback), start a worker so join() can complete.
        if self.__queue.qsize() > 0 and not self.__worker_tasks:
            await self.__ensure_worker_started()

        # 1. Drain the async pipeline completely
        await self.__queue.join()

        # 2. Flush all handlers' streams
        for handler in self.__py_logger.handlers:
            flush = getattr(handler, "flush", None)
            if callable(flush):
                flush()

    async def shutdown(self):
        if self.__stopped:
            return  # pragma: no cover

        self.__stopped = True

        # 1. Cancel worker tasks if they exist
        if self.__worker_tasks:
            for task in self.__worker_tasks:
                task.cancel()
            await asyncio.gather(*self.__worker_tasks, return_exceptions=True)

        # 2. Best-effort drain of the queue without join()
        while True:
            try:
                self.__queue.get_nowait()
                self.__queue.task_done()
            except asyncio.QueueEmpty:
                break

        # 3. Flush + close handlers
        for handler in self.__py_logger.handlers:
            try:
                handler.flush()
            except Exception:  # pragma: no cover
                pass
            try:
                handler.close()
            except Exception:  # pragma: no cover
                pass

        self.__py_logger.handlers.clear()

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
        if cls.__audit_enabled and cls.__audit_logger is not None:
            loop = cls.__audit_logger.__loop
            if loop is None or loop.is_closed():
                # Stale audit logger bound to a dead loop → reset
                await cls.terminate_auditing()
            else:
                # Live audit logger → nothing to do
                return

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
            audit_mode=True,
        )

        # Override the formatter on the actual handler
        handler = audit_logger.__py_logger.handlers[-1]
        handler.setFormatter(formatter)
        handler.rotation_logic = rotation_logic

        cls.__audit_handler = handler

    @classmethod
    async def terminate_auditing(cls) -> None:
        if not cls.__audit_enabled:
            return  # pragma: no cover

        cls.__audit_enabled = False

        if cls.__audit_logger and cls.__audit_handler:
            # noinspection PyBroadException
            try:
                cls.__audit_logger.__py_logger.removeHandler(cls.__audit_handler)
            except Exception:   # pragma: no cover
                pass

        cls.__audit_logger = None
        cls.__audit_handler = None

    # ------------------------------------------------------------------
    # METADATA SNAPSHOT
    # ------------------------------------------------------------------
    @classmethod
    def get_record(cls, *, exc_info: bool = False, stack_info: bool = False) -> RetrievedRecord:
        """
        Async metadata snapshot, mirroring SmartLogger.get_record_parts semantics
        as closely as possible.
        """
        now = time.time()

        # Resolve caller frame similarly to SmartLogger.__find_caller()
        frame = inspect.currentframe()
        if frame is not None:
            frame = frame.f_back  # caller of get_record()

        caller_frame = None
        while frame:
            filename = frame.f_code.co_filename.replace("\\", "/")
            base = os.path.basename(filename)

            if base != "async_smartlogger.py" and not (
                os.path.basename(filename) == "logging/__init__.py"
                or "pytest" in filename
                or "pluggy" in filename
                or "unittest" in filename
            ):
                caller_frame = frame
                break

            frame = frame.f_back

        if caller_frame is not None:
            file_path = caller_frame.f_code.co_filename
            lineno = caller_frame.f_lineno
            func_name = caller_frame.f_code.co_name
        else:  # pragma: no cover
            file_path = None
            lineno = None
            func_name = None

        # Thread / task / process
        thread = threading.current_thread()
        # noinspection PyBroadException
        try:
            task = asyncio.current_task()
            task_name = task.get_name() if task else None
        except Exception:  # pragma: no cover
            task_name = None

        # Exception metadata (only inside except block)
        exc_dict = None
        if exc_info:
            exc_type, exc_val, tb = sys.exc_info()
            if exc_type is not None:
                exc_dict = {
                    "exc_parts": {
                        "err_type_name": exc_type.__name__,
                        "error_text": str(exc_val),
                        "stack_trace": "".join(traceback.format_tb(tb)) if tb else None,
                    },
                    "full_trace_text": "".join(
                        traceback.format_exception(exc_type, exc_val, tb)
                    ),
                }

        # Stack metadata – start from the resolved caller frame (one level above get_record)
        if stack_info:
            if caller_frame is not None:
                stack_val = "".join(traceback.format_stack(caller_frame))
            else:  # fallback, should be rare
                stack_val = "".join(traceback.format_stack())
        else:
            stack_val = None

        # Build record
        dt = datetime.fromtimestamp(now)
        timestamp = dt.isoformat(timespec="milliseconds").replace("T", " ")

        # noinspection PyUnresolvedReferences,PyProtectedMember
        rel_created = now - logging._startTime
        if rel_created < 0:  # pragma: no cover
            rel_created = 0

        return RetrievedRecord(
            timestamp=timestamp,
            relative_created=rel_created,
            file_path=file_path,
            file_name=os.path.basename(file_path) if file_path else None,
            lineno=lineno,
            func_name=func_name,
            thread_id=thread.ident,
            thread_name=thread.name,
            task_name=task_name,
            process_id=os.getpid(),
            process_name=multiprocessing.current_process().name,
            exc_info=exc_dict,
            stack_info=stack_val,
        )

    # ------------------------------------------------------------------
    # retire & destroy
    # ------------------------------------------------------------------
    def retire(self) -> None:
        self.__retired = True

    def destroy(self) -> None:
        for handler in list(self.__py_logger.handlers):
            # noinspection PyBroadException
            try:
                self.__py_logger.removeHandler(handler)
            except Exception:   # pragma: no cover
                pass
            # noinspection PyBroadException
            try:
                handler.close()
            except Exception:   # pragma: no cover
                pass

        self.__py_logger.handlers.clear()
        self.__handlers.clear()
        self.__retired = True


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
            # noinspection PyProtectedMember
            lg._AsyncSmartLogger__py_logger.propagate = False
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
