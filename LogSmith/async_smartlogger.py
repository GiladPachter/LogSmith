# LogSmith/async_smartlogger.py

from __future__ import annotations

import asyncio
import inspect
import logging
import multiprocessing
import sys
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, ClassVar, Dict, Optional
import json
import os
import threading
import time

from .formatter import (
    StructuredPlainFormatter,
    StructuredColorFormatter,
    PassthroughFormatter,
    AuditFormatter,
    LogRecordDetails,
)
from .levels import TRACE, LevelStyle
from .level_registry import LEVELS
from .colors import CPrint
from .rotation import RotationLogic
from .async_rotation import Async_TimedSizedRotatingFileHandler
from .smartlogger import RetrievedRecord


class AsyncOp(Enum):
    LOG = auto()
    RAW = auto()
    ROTATE = auto()
    SENTINEL = auto()


@dataclass
class _QueueItem:
    op: AsyncOp
    payload: dict[str, Any]


@dataclass
class AsyncHandlerInfo:
    kind: str                      # "console" | "file"
    level: str
    path: Optional[str] = None
    rotation: Optional[dict] = None
    do_not_sanitize_colors_from_string: Optional[bool] = None


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

    __instances: ClassVar[Dict[str, "AsyncSmartLogger"]] = {}
    __default_level: ClassVar[int] = logging.INFO

    # auditing state
    __audit_enabled: ClassVar[bool] = False
    __audit_logger: ClassVar[Optional["AsyncSmartLogger"]] = None
    __audit_handler: ClassVar[Optional[logging.Handler]] = None

    __messages_processed: ClassVar[int] = 0

    @classmethod
    def messages_processed(cls) -> int:
        return cls.__messages_processed

    def queue_depth(self) -> int:
        return self._queue.qsize()

    # ------------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------------
    def __init__(self, name: str, level: int) -> None:
        self._name = name
        self._level = level

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

        self._handlers: list[AsyncHandlerInfo] = []
        self._real_handlers: list[logging.Handler] = []

        self._retired = False

        self._start_worker()

    # ------------------------------------------------------------------
    # FACTORY
    # ------------------------------------------------------------------
    @classmethod
    def get(cls, name: str, level: int) -> "AsyncSmartLogger":
        if name in cls.__instances:
            logger = cls.__instances[name]
            logger.set_level(level)
            return logger

        inst = cls(name, level)
        cls.__instances[name] = inst
        return inst

    # ------------------------------------------------------------------
    # WORKER
    # ------------------------------------------------------------------
    def _start_worker(self) -> None:
        if self._worker_task is not None:
            return
        self._worker_task = self._loop.create_task(self._worker())

    async def _worker(self) -> None:
        while True:
            item = await self._queue.get()
            try:
                if item.op is AsyncOp.SENTINEL:
                    return

                if item.op is AsyncOp.LOG:
                    await self._process_log(item.payload)
                elif item.op is AsyncOp.RAW:
                    await self._process_raw(item.payload)
                elif item.op is AsyncOp.ROTATE:
                    await self._process_rotate(item.payload)
            finally:
                self._queue.task_done()

    # ------------------------------------------------------------------
    # PROCESS LOG
    # ------------------------------------------------------------------
    async def _process_log(self, payload: dict[str, Any]) -> None:
        level: int = payload["level"]
        msg: str = payload["msg"]
        args: tuple[Any, ...] = payload["args"]
        extra: dict[str, Any] = payload["extra"]
        fields: dict[str, Any] = payload["fields"]
        exc_info = payload["exc_info"]
        stack_info_flag: bool = payload["stack_info_flag"]

        if fields:
            extra.setdefault("fields", {}).update(fields)

        frame = self._find_caller()
        pathname = frame.f_code.co_filename
        lineno = frame.f_lineno
        func_name = frame.f_code.co_name

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
                level, msg, args, audit_extra, {}, exc_info=None, stack_info_flag=False
            )

        record_name = extra.pop("force_logger_name", self._name)

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
        record.__dict__.update(extra)

        await asyncio.to_thread(self._py_logger.handle, record)

        AsyncSmartLogger.__messages_processed += 1

    # ------------------------------------------------------------------
    # PROCESS RAW
    # ------------------------------------------------------------------
    async def _process_raw(self, payload: dict[str, Any]) -> None:
        message: str = payload["message"]
        end: str = payload["end"]

        def write_raw() -> None:
            for handler in self._py_logger.handlers:
                stream = getattr(handler, "stream", None)

                if stream is None and hasattr(handler, "_open"):
                    try:
                        handler.stream = handler._open()
                        stream = handler.stream
                    except Exception:
                        continue

                if stream is None:
                    continue

                is_console = isinstance(handler, logging.StreamHandler) and not isinstance(
                    handler, Async_TimedSizedRotatingFileHandler
                )

                if is_console:
                    text = self._bleach_non_colored_text(message)
                else:
                    do_not_sanitize = getattr(handler, "do_not_sanitize_colors_from_string", False)
                    text = message if do_not_sanitize else CPrint.strip_ansi(message)

                try:
                    stream.write(text + end)
                    stream.flush()
                except Exception:
                    continue

        await asyncio.to_thread(write_raw)

    # ------------------------------------------------------------------
    # PROCESS ROTATION
    # ------------------------------------------------------------------
    @staticmethod
    async def _process_rotate(payload: dict[str, Any]) -> None:
        handler: Async_TimedSizedRotatingFileHandler = payload["handler"]
        await asyncio.to_thread(handler.perform_rotation)

    # ------------------------------------------------------------------
    # CALLER RESOLUTION
    # ------------------------------------------------------------------
    @staticmethod
    def _find_caller():
        stack = inspect.stack()

        for frame_info in stack[2:]:
            frame = frame_info.frame
            code = frame.f_code
            filename = code.co_filename

            if filename.startswith("<"):
                continue

            if "asyncio" in filename.replace("\\", "/"):
                continue

            module = frame.f_globals.get("__name__", "")
            if module.startswith("LogSmith.async_smartlogger"):
                continue

            return frame

        return stack[1].frame

    # ------------------------------------------------------------------
    # RAW COLOR BLEACHING
    # ------------------------------------------------------------------
    @staticmethod
    def _bleach_non_colored_text(message: str) -> str:
        result: list[str] = []
        plain_buffer: list[str] = []

        i = 0
        n = len(message)
        color_active = False

        def flush_plain():
            if not plain_buffer:
                return
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

    def set_level(self, level: int) -> None:
        self._level = level
        self._py_logger.setLevel(level)

    # ------------------------------------------------------------------
    # PUBLIC: HANDLER MANAGEMENT
    # ------------------------------------------------------------------
    def add_console(
        self,
        level: int = TRACE,
        log_record_details: Optional[LogRecordDetails] = None,
        formatter: Optional[logging.Formatter] = None,
    ) -> None:
        if self._retired:
            raise RuntimeError(f"AsyncSmartLogger {self._name!r} has been retired and cannot accept handlers.")

        if log_record_details is None:
            log_record_details = LogRecordDetails()

        handler = logging.StreamHandler()
        handler.setLevel(level)

        if formatter is None:
            formatter = StructuredColorFormatter(log_record_details)

        handler.setFormatter(formatter)
        self._py_logger.addHandler(handler)

        level_name = logging.getLevelName(level)
        self._handlers.append(AsyncHandlerInfo(kind="console", level=level_name))
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
        formatter: Optional[logging.Formatter] = None,
    ) -> None:
        if self._retired:
            raise RuntimeError(f"AsyncSmartLogger {self._name!r} has been retired and cannot accept handlers.")

        normalized = os.path.abspath(os.path.normpath(log_dir))
        if log_dir != normalized:
            raise ValueError(
                f"for avoiding human errors, log_dir must be normalized. "
                f"Got '{log_dir}', where normalized log_dir is '{normalized}'."
            )

        os.makedirs(normalized, exist_ok=True)
        log_dir_path = Path(normalized).resolve()
        os.makedirs(log_dir_path, exist_ok=True)

        file_path = log_dir_path / logfile_name
        resolved_path = str(file_path.resolve())

        if formatter is None:
            if do_not_sanitize_colors_from_string:
                formatter = PassthroughFormatter()
            else:
                formatter = StructuredPlainFormatter(log_record_details)

        if rotation_logic:
            handler = Async_TimedSizedRotatingFileHandler(
                baseFilename=str(file_path),
                rotation_logic=rotation_logic,
            )
        else:
            handler = logging.FileHandler(str(file_path), encoding="utf-8")

        handler.setLevel(level or self._level)
        handler.setFormatter(formatter)

        setattr(handler, "do_not_sanitize_colors_from_string", do_not_sanitize_colors_from_string)

        if isinstance(handler, Async_TimedSizedRotatingFileHandler):
            handler.rotation_callback = self.__enqueue_rotation
            handler.resolved_path = resolved_path

        self._py_logger.addHandler(handler)

        level_name = logging.getLevelName(level or self._level)
        rotation_meta = None
        if rotation_logic:
            rotation_meta = {
                "maxBytes": rotation_logic.maxBytes,
                "when": rotation_logic.when.name if rotation_logic.when else None,
                "interval": rotation_logic.interval,
                "backupCount": rotation_logic.backupCount,
            }

        self._handlers.append(
            AsyncHandlerInfo(
                kind="file",
                level=level_name,
                path=resolved_path,
                rotation=rotation_meta,
                do_not_sanitize_colors_from_string=do_not_sanitize_colors_from_string,
            )
        )
        self._real_handlers.append(handler)

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

    @property
    def handler_info(self) -> list[dict[str, Any]]:
        info: list[dict[str, Any]] = []
        for h in self._handlers:
            d = asdict(h)
            if d["kind"] == "console":
                d.pop("path", None)
                d.pop("rotation", None)
                d.pop("do_not_sanitize_colors_from_string", None)
            info.append(d)
        return info

    @property
    def handler_info_json(self) -> str:
        return json.dumps(self.handler_info, indent=4)

    @property
    def output_targets(self) -> list[dict[str, Any]]:
        return self.handler_info

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
    ) -> None:
        if self._stopped:
            raise RuntimeError("AsyncSmartLogger has been shut down.")
        if self._retired:
            raise RuntimeError(f"AsyncSmartLogger {self._name!r} has been retired and cannot be used.")

        await self._queue.put(
            _QueueItem(
                op=AsyncOp.LOG,
                payload={
                    "level": level,
                    "msg": msg,
                    "args": args,
                    "extra": extra,
                    "fields": fields,
                    "exc_info": exc_info,
                    "stack_info_flag": stack_info_flag,
                },
            )
        )

    async def _enqueue_raw(self, message: str, end: str) -> None:
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

    def __enqueue_rotation(self, handler: Async_TimedSizedRotatingFileHandler) -> None:
        if self._stopped or self._retired:
            return

        if not self._py_logger.handlers:
            return

        self._loop.call_soon_threadsafe(
            self._queue.put_nowait,
            _QueueItem(op=AsyncOp.ROTATE, payload={"handler": handler}),
        )

    # ------------------------------------------------------------------
    # PUBLIC: ASYNC LOGGING API
    # ------------------------------------------------------------------
    async def a_log(self, level: int, msg: str, *args, **kwargs) -> None:
        if self._retired:
            raise RuntimeError(f"AsyncSmartLogger {self._name!r} has been retired and cannot be used.")

        if not self._py_logger.isEnabledFor(level):
            return

        exc_info_flag = kwargs.pop("exc_info", False)
        stack_info_flag = kwargs.pop("stack_info", False)

        captured_exc = sys.exc_info() if exc_info_flag else None

        extra = kwargs.pop("extra", {}) or {}
        fields = kwargs

        await self._enqueue_log(
            level,
            msg,
            args,
            extra,
            fields,
            exc_info=captured_exc,
            stack_info_flag=stack_info_flag,
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
        await self._enqueue_raw(message, end)

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
            raise ValueError(f"Level '{name}' already exists")

        for meta in LEVELS.all().values():
            if meta["value"] == value:
                raise ValueError(f"Level value '{value}' already exists")

        if value < 0:
            raise ValueError("Negative level values are reserved for internal operations")

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
            return

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
                continue

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
        if self._stopped:
            raise RuntimeError("AsyncSmartLogger has been shut down.")
        await self._queue.join()

    async def shutdown(self) -> None:
        if self._stopped:
            return
        self._stopped = True

        await self._queue.join()
        await self._queue.put(_QueueItem(op=AsyncOp.SENTINEL, payload={}))

        if self._worker_task is not None:
            await self._worker_task

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
            return

        cls.__audit_enabled = True

        audit_logger = cls.get("_async_audit", cls.__default_level)
        cls.__audit_logger = audit_logger

        if details is None:
            details = LogRecordDetails()

        formatter = AuditFormatter(details)

        audit_logger.add_file(
            log_dir=log_dir,
            logfile_name=logfile_name,
            rotation_logic=rotation_logic,
            formatter=formatter,
        )

        cls.__audit_handler = audit_logger._py_logger.handlers[-1]

    @classmethod
    async def terminate_auditing(cls) -> None:
        if not cls.__audit_enabled:
            return

        cls.__audit_enabled = False

        if cls.__audit_logger and cls.__audit_handler:
            try:
                cls.__audit_logger._py_logger.removeHandler(cls.__audit_handler)
            except Exception:
                pass

        cls.__audit_logger = None
        cls.__audit_handler = None

    # ------------------------------------------------------------------
    # METADATA SNAPSHOT
    # ------------------------------------------------------------------
    @classmethod
    def get_record(cls, *, exc_info: bool = False, stack_info: bool = False) -> RetrievedRecord:
        now = datetime.now()

        frame = inspect.stack()[1]
        frame_info = frame.frame
        file_path = frame_info.f_code.co_filename
        file_name = os.path.basename(file_path)
        lineno = frame_info.f_lineno
        func_name = frame_info.f_code.co_name

        thread = threading.current_thread()
        task = asyncio.current_task()

        exc = None
        if exc_info:
            exc_type, exc_val, tb = sys.exc_info()
            if exc_type:
                exc = {
                    "type": exc_type.__name__,
                    "message": str(exc_val),
                    "traceback": traceback.format_exception(exc_type, exc_val, tb),
                }

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
            try:
                self._py_logger.removeHandler(handler)
            except Exception:
                pass
            try:
                handler.close()
            except Exception:
                pass

        self._real_handlers.clear()
        self._handlers.clear()
        self._retired = True
