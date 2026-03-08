# LogSmith/LogSmith.py

from __future__ import annotations
import inspect
import json
import logging
import os
import sys
import time
import threading
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Protocol, Literal, Callable, List, Dict, ClassVar

from .formatter import (
    StructuredPlainFormatter,
    StructuredColorFormatter,
    LogRecordDetails, PassthroughFormatter, AuditFormatter, OutputMode, StructuredJSONFormatter,
    StructuredNDJSONFormatter, OptionalRecordFields,
)
from .levels import LevelStyle, TRACE
from .level_registry import LEVELS
from .colors import CPrint
from .rotation import RotationLogic

"""
console printing utility
"stdout()" function replaces print()
it has the same effect, only it synchronizes with console logs
"""
import io
import contextlib


class _SmartLoggerState:
    """
    Internal state holder for SmartLogger-specific data.
    """

    def __init__(self) -> None:
        self.handlers: list[HandlerMetadata] = []
        self.retired: bool = False


# ======================================================================
#  Strongly-Typed result returned by SmartLogger.get_record()
# ======================================================================
@dataclass
class RetrievedRecord:
    # core
    timestamp: str | None = None
    level: str | None = None

    # optional fields
    relative_created: float | None = None
    logger_name: str | None = None
    file_path: str | None = None
    file_name: str | None = None
    lineno: int | None = None
    func_name: str | None = None
    thread_id: int | None = None
    thread_name: str | None = None
    task_name: str | None = None
    process_id: int | None = None
    process_name: str | None = None

    # diagnostics
    exc_info: dict | None = None
    stack_info: str | List[str] | None = None


@dataclass
class HandlerMetadata:
    kind: str
    level: str
    formatter: str
    path: Optional[str] = None
    rotation: Optional[Dict[str, Any]] = None
    do_not_sanitize_colors_from_string: Optional[bool] = None


# ======================================================================
#  SMARTLOGGER IMPLEMENTATION
# ======================================================================
class SmartLogger:
    """
    SmartLogger
    ===========
    A high‑level logging framework that unifies console output, file logging,
    auditing, rotation, formatting, and ANSI/gradient colorization into a single,
    consistent API.

    SmartLogger wraps Python's standard logging module but adds:
        • Automatic, centralized initialization
        • Named loggers with independent levels
        • Console and file handlers with easy and consistent formatting
        • Structured log record details (process, thread, file, line, etc.)
        • Size‑based, time‑based, and hybrid rotation via RotationLogic
        • Full auditing mode that captures *all* loggers in the process
        • ANSI color output and 256‑color gradients (via CPrint)
        • Thread‑safe, process‑safe rotating file handlers
        • A simple, expressive API for raw output (SmartLogger.raw)

    ✔ SmartLogger supports:
        • single‑process applications
        • multi‑threaded applications
        • multi‑process applications writing to separate log files
        • multi‑process applications writing to a shared log directory
        • rotation (size/time/combined)
        • retention
        • concurrency safety within a process
        • cross‑platform correctness

    ✔ SmartLogger does not support:
        • multiple processes writing to the same base log file on Windows

    ---------------------------------------------------------------------------
    Creating loggers
    ---------------------------------------------------------------------------
    SmartLogger(name, level=None)
        Returns a SmartLogger instance bound to the given name.
        Each logger may have its own level and its own handlers.

    ---------------------------------------------------------------------------
    Handlers
    ---------------------------------------------------------------------------
    add_console(level: int, log_record_details: LogRecordDetails)
        Adds a color‑capable console handler.

    add_file(log_dir, logfile_name, level=..., rotation_logic=None)
        Adds a file handler with optional rotation.
        RotationLogic supports:
            • when                      (time-based rotation rule: H / M / S / every day / chosen weekday)
            • interval                  (H / M / S  time units between rotations)
            • RotationTimestamp         (time in the day to rotate)
            • maxBytes                  (size‑based)
            • backupCount               (how many files in the rotation)
            • append_filename_timestamp ( . . . to rotating file names)

    ---------------------------------------------------------------------------
    Formatting
    ---------------------------------------------------------------------------
    LogRecordDetails + OptionalRecordFields allow fine‑grained control over:
        • timestamp formatting
        • which metadata fields appear (logger name, file, line, thread, process)
        • the order of message components

    ---------------------------------------------------------------------------
    Color & Gradient Support
    ---------------------------------------------------------------------------
    SmartLogger integrates with CPrint to provide:
        • Solid ANSI colors (foreground/background)
        • Intensity (bold, dim)
        • Styles (underline, italic, strike, reverse)
        • 256‑color gradients (horizontal, vertical, reverse, auto)
        • Combined foreground + background gradients
        • Named palettes (GradientPalette)
        • Palette blending utilities

    ---------------------------------------------------------------------------
    Raw output
    ---------------------------------------------------------------------------
    raw(text)
        Writes text directly to the console handler without formatting.
        Supports full ANSI color and gradient output via CPrint.

    ---------------------------------------------------------------------------
    Thread/process safety
    ---------------------------------------------------------------------------
    File handlers use a concurrent‑safe rotating handler implementation that
    avoids corruption under multi‑threaded or multi‑process workloads.

    ---------------------------------------------------------------------------
    Auditing
    ---------------------------------------------------------------------------
    SmartLogger.audit_everything(log_dir, logfile_name, rotation_logic, details)
        Installs a global handler that receives *every* log record emitted by
        any logger in the process. Useful for debugging, compliance, and
        post‑mortem analysis.

    SmartLogger.terminate_auditing()
        Removes the global audit handler.

    ---------------------------------------------------------------------------
    Summary
    ---------------------------------------------------------------------------
    SmartLogger is designed to be a drop‑in replacement for Python's logging
    module when you want:
        • cleaner APIs
        • richer formatting
        • safer rotation
        • global auditing
        • colorized and gradient‑enhanced console output
        • predictable behavior across an entire application

    It is suitable for CLI tools, services, daemons, debugging utilities,
    and any application that benefits from structured, readable, and
    visually expressive logging.
    """

    __audit_handler: ClassVar[Optional[logging.Handler]] = None
    __audit_enabled: bool = False
    __audit_details: LogRecordDetails | None = None

    __file_handler_lock = threading.RLock()

    def __init__(self, name: str, level: int = logging.NOTSET) -> None:
        self._smart_state = _SmartLoggerState()

        self._name = name

        self._py_logger = logging.getLogger(name)
        self._py_logger.propagate = False
        self._py_logger.setLevel(level)

        # Register this logger in the global logging manager so that
        # logging.getLogger(name) returns THIS instance from now on.
        manager = logging.Logger.manager

        # Restore natural logging hierarchy:
        #   "myapp.api.users" -> parent "myapp"
        #   "myapp"           -> parent "root"
        if "." in name:
            parent_name = name.rpartition(".")[0]
            parent = manager.loggerDict.get(parent_name)
            if parent is None:
                parent = logging.getLogger(parent_name)
            self._py_logger.parent = parent
        else:
            self._py_logger.parent = logging.getLogger()  # root

        # Set this logger's own level
        self._py_logger.setLevel(level)

        # Auditing still controls propagation
        self._py_logger.propagate = SmartLogger.__audit_enabled

    def trace(self, msg, *args, **kwargs):
        self.__log(TRACE, msg, args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.__log(logging.DEBUG, msg, args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.__log(logging.INFO, msg, args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.__log(logging.WARNING, msg, args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.__log(logging.ERROR, msg, args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.__log(logging.CRITICAL, msg, args, **kwargs)

    @property
    def name(self) -> str:
        return self._name

    @property
    def level(self) -> int:
        return self._py_logger.level

    @level.setter
    def level(self, value) -> None:
        self._py_logger.setLevel(value)

    @staticmethod
    def __bleach_non_colored_text(message: str) -> str:
        """
        Isolating non-colored text and coloring it with console default.
        """
        result: list[str] = []
        plain_buffer: list[str] = []

        i = 0
        n = len(message)
        color_active = False  # True between non-reset code and its reset

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

            if ch == "\x1b":  # ESC → start of ANSI sequence
                if not color_active:
                    flush_plain()

                start = i
                i += 1
                while i < n and message[i] != "m":
                    i += 1
                i += 1  # include 'm'

                seq = message[start:i]
                result.append(seq)

                # Update color_active
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

    def raw(self, message: str, end: str = "\n") -> None:
        """
        Write raw text to all handlers.
        Console handlers receive colored output.
        File handlers sanitize ANSI unless do_not_sanitize_colors_from_string=True.
        """
        if self._smart_state.retired:
            raise RuntimeError(f"Logger {self._py_logger.name!r} has been retired and cannot be used.")

        for handler in self._py_logger.handlers:
            stream = getattr(handler, "stream", None)

            # FIX: FileHandler lazily opens the file; force-open if needed
            if stream is None and hasattr(handler, "baseFilename"):
                try:
                    handler.acquire()
                    # noinspection PyUnresolvedReferences,PyProtectedMember
                    handler.stream = handler._open()
                finally:
                    handler.release()
                stream = handler.stream

            # Still no stream? Skip this handler
            if stream is None:
                continue

            is_console = isinstance(handler, logging.StreamHandler) and not hasattr(handler, "baseFilename")

            if is_console:
                # Console: bleach non-colored text
                text = self.__bleach_non_colored_text(message)
            else:
                # File: sanitize unless passthrough enabled
                do_not_sanitize = getattr(handler, "do_not_sanitize_colors_from_string", False)
                text = message if do_not_sanitize else CPrint.strip_ansi(message)

            stream.write(text + end)
            stream.flush()

    # ------------------------------------------------------------------
    #  CORE LOGGING BEHAVIOR
    # ------------------------------------------------------------------
    @staticmethod
    def __find_caller():
        frame = inspect.currentframe()
        # Skip frames until we reach user code
        while frame:
            code = frame.f_code
            filename = code.co_filename.replace("\\", "/")

            # Skip SmartLogger internals
            if "smartlogger.py" in filename:
                frame = frame.f_back
                continue

            # Skip Python logging internals
            if "/logging/" in filename or filename.endswith("logging/__init__.py"):
                frame = frame.f_back
                continue

            # This is user code
            return frame

        return None

    def __log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1, **kwargs):
        if self._smart_state.retired:
            raise RuntimeError(f"Logger {self._name!r} has been retired and cannot be used.")

        # Level filtering (hierarchy-aware)
        if not self._py_logger.isEnabledFor(level):
            return

        if extra is None:
            extra = {}

        if kwargs:
            extra["fields"] = kwargs

        if exc_info is True:
            exc_info = sys.exc_info()

        # Resolve caller
        frame = self.__find_caller()
        pathname = frame.f_code.co_filename
        lineno = frame.f_lineno
        func_name = frame.f_code.co_name

        sinfo = "".join(traceback.format_stack()) if stack_info else None

        # Build LogRecord
        record = logging.LogRecord(
            name=self._name,
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

        # AUDIT
        if SmartLogger.__audit_enabled and SmartLogger.__audit_handler:
            SmartLogger.__audit_handler.handle(record)

        # Let Python logging handle hierarchy + filtering + propagation
        self._py_logger.handle(record)

    def __wrap_builtin(self, level_value: int) -> Callable[..., None]:
        def log_method(msg=None, *args, stacklevel=2, **kwargs):
            if msg is None:
                msg = ""
            if self._py_logger.isEnabledFor(level_value):
                self.__log(level_value, msg, args, stacklevel=stacklevel, **kwargs)

        return log_method

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
        if self._smart_state.retired:
            raise RuntimeError(f"Logger {self._py_logger.name!r} has been retired and cannot accept handlers.")

        if any([1 for info in self.handler_info if info["kind"] == "console"]):
            raise RuntimeError(f"Logger {self._py_logger.name!r} already has a console handler.")

        mode: OutputMode = self.__normalize_output_mode(output_mode)

        # Ensure we have a LogRecordDetails instance
        if log_record_details is None:
            log_record_details = LogRecordDetails()

        # Ensure optional_record_fields exists
        if log_record_details.optional_record_fields is None:
            log_record_details.optional_record_fields = OptionalRecordFields()

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

        self._smart_state.handlers.append(
            HandlerMetadata(
                kind="console",
                level=logging.getLevelName(level),
                formatter=str(mode.value),
            )
        )

    def remove_console(self) -> None:
        """
        Remove the console handler previously added with add_console().
        Raises:
            RuntimeError: if no console handler exists.
        """
        for h in list(self._py_logger.handlers):
            if isinstance(h, logging.StreamHandler) and not hasattr(h, "baseFilename"):
                self._py_logger.removeHandler(h)
                h.close()
                break
        else:
            raise RuntimeError(f"Logger {self._py_logger.name!r} has no console handler to remove.")

            # Remove metadata
        self._smart_state.handlers = [
            info for info in self._smart_state.handlers
            if info.kind != "console"
        ]

    def add_file(
            self,
            log_dir: str,
            logfile_name: str | None = None,
            level: int | None = None,
            log_record_details: LogRecordDetails | None = None,
            rotation_logic: RotationLogic | None = None,
            do_not_sanitize_colors_from_string: bool = False,
            output_mode: str | OutputMode = OutputMode.PLAIN,
    ) -> None:
        if self._smart_state.retired:
            raise RuntimeError(f"Logger {self._py_logger.name!r} has been retired and cannot accept handlers.")

        mode = self.__normalize_output_mode(output_mode)

        # verify normalized log_dir given
        normalized = os.path.abspath(os.path.normpath(log_dir))
        if log_dir != normalized:
            raise ValueError(
                f"for avoiding human errors, log_dir must be normalized. "
                f"Got '{log_dir}', where normalized log_dir is '{normalized}'."
            )

        # --- PREP WORK (outside lock) -------------------------------------
        os.makedirs(normalized, exist_ok=True)

        log_dir_path = Path(log_dir).resolve()
        os.makedirs(log_dir_path, exist_ok=True)

        if logfile_name is None:
            logfile_name = f"{self._py_logger.name}.log"

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

        # Create the handler
        if rotation_logic:
            handler = rotation_logic.create_handler(str(file_path))
        else:
            handler = logging.FileHandler(str(file_path), encoding="utf-8")

        handler.setLevel(level or self._py_logger.level)
        handler.setFormatter(formatter)

        handler.log_record_details = log_record_details
        handler.rotation_logic = rotation_logic
        handler.do_not_sanitize_colors_from_string = do_not_sanitize_colors_from_string

        # --- CRITICAL SECTION (tight lock) --------------------------------
        with SmartLogger.__file_handler_lock:

            # 1. Check all SmartLogger instances for duplicate file handlers
            for logger in logging.Logger.manager.loggerDict.values():
                if not isinstance(logger, SmartLogger):
                    continue

                for info in logger._smart_state.handlers:
                    if info.kind != "file" or not info.path:
                        continue

                    existing_resolved = str(Path(info.path).resolve())
                    if existing_resolved == resolved_path:
                        raise ValueError(
                            f"A file handler for '{resolved_path}' is already active "
                            f"in this process. This is usually caused by a duplicate "
                            f"configuration or copy‑paste error."
                        )

            # 2. Safe to attach
            self._py_logger.addHandler(handler)

            # 3. Track metadata
            rotation_meta = (
                {
                    "maxBytes": rotation_logic.maxBytes,
                    "when": rotation_logic.when.name if rotation_logic.when else None,
                    "interval": rotation_logic.interval,
                    "backupCount": rotation_logic.backupCount,
                }
                if rotation_logic else None
            )

            self._smart_state.handlers.append(
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
        """
        Remove a specific file handler identified by (logfile_name, log_dir).

        Args:
            logfile_name: The name of the log file (e.g., "app.log").
            log_dir: The absolute directory path where the log file resides.

        Raises:
            RuntimeError: if no matching file handler exists.
        """
        target_path = str(Path(log_dir, logfile_name).resolve())

        removed = False
        for h in list(self._py_logger.handlers):
            if isinstance(h, logging.FileHandler) and Path(h.baseFilename).resolve() == Path(target_path):
                self._py_logger.removeHandler(h)
                h.close()
                removed = True
                break

        if not removed:
            raise RuntimeError(
                f"Logger {self._py_logger.name!r} has no file handler for "
                f"log_dir={log_dir!r}, logfile_name={logfile_name!r}."
            )

        self._smart_state.handlers = [
            info for info in self._smart_state.handlers
            if not (info.kind == "file" and info.path == target_path)
        ]

    # ------------------------------------------------------------------
    #  HANDLER INTROSPECTION (READ-ONLY)
    # ------------------------------------------------------------------

    @staticmethod
    def __pretty_handler_info(info: HandlerMetadata) -> dict[str, Any]:
        """
        Convert HandlerInfo into a clean, human‑readable dict.
        Includes the handler object itself so that removal operations
        can be performed safely and unambiguously.
        """
        base: dict[str, Any] = {
            "kind": info.kind,
            "level": logging.getLevelName(info.level),
            "formatter": info.formatter,
        }

        if info.kind == "file":
            base["path"] = info.path
            base["rotation"] = (
                {
                    "maxBytes": info.rotation_logic.maxBytes,
                    "when": info.rotation_logic.when,
                    "interval": info.rotation_logic.interval,
                    "backupCount": info.rotation_logic.backupCount,
                }
                if info.rotation_logic
                else None
            )
            base["do_not_sanitize_colors_from_string"] = info.do_not_sanitize_colors_from_string

        return base

    @property
    def handler_info(self) -> list[dict[str, Any]]:
        return [asdict(h) for h in self._smart_state.handlers]

    @property
    def console_handler(self):
        for h in self._smart_state.handlers:
            if h.kind == "console":
                return asdict(h)
        return None

    @property
    def file_handlers(self):
        return [asdict(h) for h in self._smart_state.handlers if h.kind == "file"]

    @property
    def output_targets(self) -> list[str]:
        out_targets = []
        for info in self._smart_state.handlers:
            if info.kind == "console":
                out_targets.append("console")
            else:
                out_targets.append(info.path)

        return out_targets

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
    #  LEVEL REGISTRY HELPERS
    # ------------------------------------------------------------------
    @staticmethod
    def levels() -> dict[str, int]:
        levels = {"NOTSET": logging.NOTSET}
        for name, meta in LEVELS.all().items():
            levels[name] = meta["value"]
        return levels

    @staticmethod
    def __safeguard_internals(name: str, value: int):
        # Prevent overriding internal SmartLogger attributes
        if name in SmartLogger.__dict__:
            raise ValueError(f"Cannot override internal SmartLogger attribute '{name}'")

        # Prevent duplicate level names
        if name in LEVELS.all():
            raise ValueError(f"Level '{name}' already exists")

        # Prevent duplicate numeric values
        for meta in LEVELS.all().values():
            if meta["value"] == value:
                raise ValueError(f"Level value '{value}' already exists")

        # Prevent negative values (reserved for internal operations)
        if value < 0:
            raise ValueError("Negative level values are reserved for internal operations")

    @staticmethod
    def register_level(name: str, value: int, style: Optional[LevelStyle] = None) -> None:
        SmartLogger.__safeguard_internals(name, value)
        LEVELS.register(name, value, style)

    @staticmethod
    def apply_color_theme(theme: dict[int, LevelStyle]) -> None:
        # Reset to defaults
        if theme is None:
            for name, meta in LEVELS.all().items():
                meta["style"] = meta["default_style"]
            return

        # Validate type
        if not isinstance(theme, dict):
            raise TypeError("Theme must be a dict mapping level numbers to LevelStyle instances")

        # Validate keys and values
        for level, style in theme.items():
            if not isinstance(level, int):
                raise TypeError(f"Theme key '{level}' must be an int (log level number)")
            if not isinstance(style, LevelStyle):
                raise TypeError(f"Theme value for level {level} must be a LevelStyle instance")

        # Apply custom theme
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
    #  RETIRE / DESTROY a logger
    # ------------------------------------------------------------------
    def retire(self) -> None:
        """
        Retire this logger:
          - close all handlers
          - remove them from the logger
          - clear metadata
          - mark logger as unusable
        """
        if self._smart_state.retired:
            return

            # Close and remove all real handlers
        for h in list(self._py_logger.handlers):
            # noinspection PyBroadException
            try:
                h.close()
            except Exception:
                pass
            # noinspection PyBroadException
            try:
                self._py_logger.removeHandler(h)
            except Exception:
                pass

        self._py_logger.handlers.clear()
        self._smart_state.handlers.clear()
        self._smart_state.retired = True

    def destroy(self) -> None:
        """
        Completely remove this logger from the logging system.

        Safe to call:
          - before retire()
          - after retire()
          - multiple times

        Guarantees:
          - All handlers are closed and removed
          - Logger is marked retired
          - Logger is removed from loggerDict
          - Logger is detached from its parent
          - Logger's children are re-parented to root
          - Logger cannot be used again
          - A new logger with the same name can be created cleanly
        """
        # 1. Ensure handlers are closed and logger is marked retired
        if not self._smart_state.retired:
            self.retire()

        # 2. Remove from loggerDict (main fingerprint)
        # noinspection PyBroadException
        try:
            logging.Logger.manager.loggerDict.pop(self._py_logger.name, None)
        except Exception:
            pass

        # 3. Detach from parent
        # noinspection PyBroadException
        try:
            self._py_logger.parent = None
        except Exception:
            pass

        # 4. Re-parent children to root (important!)
        root = logging.getLogger("root")
        for child_name, child in list(logging.Logger.manager.loggerDict.items()):
            if isinstance(child, logging.Logger) and child.parent is self._py_logger:
                child.parent = root

        # 5. Clear filters, level, and other attributes
        # noinspection PyBroadException
        try:
            self._py_logger.filters.clear()
        except Exception:
            pass

        # noinspection PyBroadException
        try:
            self._py_logger.setLevel(logging.NOTSET)
        except Exception:
            pass

        # 6. Mark as destroyed (optional but useful)
        self._smart_state.retired = True

    # ------------------------------------------------------------------
    #  DYNAMIC LEVELS VIA __getattr__
    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)

        upper = name.upper()

        if upper not in LEVELS.all():
            raise AttributeError(f"{self.__class__.__name__!s} has no attribute {name!r}")

        level_value = LEVELS.get(upper)["value"]

        def dynamic_log_method(msg: str, *args, **kwargs):
            if self._py_logger.isEnabledFor(level_value):
                self.__log(level_value, msg, args, stacklevel=2, **kwargs)

        return dynamic_log_method

    @property
    def retired(self) -> bool:
        return self._smart_state.retired

    # ------------------------------------------------------------------
    #  MISC HELPERS
    # ------------------------------------------------------------------
    @staticmethod
    def audit_everything(
        log_dir: str,
        logfile_name: str,
        rotation_logic: RotationLogic | None = None,
        details: LogRecordDetails | None = None,
    ) -> None:
        """
        Enable global auditing of all SmartLogger instances.

        All log records emitted by any SmartLogger will be duplicated into
        a single audit log file. The audit handler uses AuditFormatter,
        which preserves ANSI and formats records using the provided
        LogRecordDetails.

        Parameters
        ----------
        log_dir : str
            Directory where the audit log file will be created.
        logfile_name : str
            Name of the audit log file.
        rotation_logic : RotationLogic | None
            Optional rotation configuration.
        details : LogRecordDetails | None
            Formatting details for audit entries. If None, defaults to
            SmartLogger's global default LogRecordDetails.
        """
        if rotation_logic is not None and not isinstance(rotation_logic, RotationLogic):
            raise ValueError("rotation_logic must be a RotationLogic instance or None")

        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, logfile_name)

        # Create handler
        if rotation_logic:
            handler = rotation_logic.create_handler(file_path)
        else:
            handler = logging.FileHandler(file_path, encoding="utf-8")

        handler.setLevel(logging.NOTSET)

        # Use provided details or fallback to SmartLogger defaults
        if details is None:
            details = LogRecordDetails()

        handler.setFormatter(AuditFormatter(details))

        # Attach to root logger
        root = logging.getLogger()

        # Remove all existing handlers to avoid formatting conflicts
        for h in list(root.handlers):
            root.removeHandler(h)

        root.addHandler(handler)

        # Store state
        SmartLogger.__audit_handler = handler
        SmartLogger.__audit_enabled = True
        SmartLogger.__audit_details = details

        # Retroactively enable propagation on all SmartLogger instances
        for logger in logging.Logger.manager.loggerDict.values():
            if isinstance(logger, SmartLogger):
                logger.propagate = True

    @staticmethod
    def terminate_auditing() -> None:
        """
        Disable global auditing and remove the audit handler from the root logger.
        Retroactively disables propagation on all SmartLogger instances.
        Safe to call even if auditing is not active.
        """
        if not SmartLogger.__audit_enabled:
            return

        root = logging.getLogger()
        if SmartLogger.__audit_handler in root.handlers:
            root.removeHandler(SmartLogger.__audit_handler)

        SmartLogger.__audit_handler = None
        SmartLogger.__audit_enabled = False
        SmartLogger.__audit_details = None

        # Retroactively disable propagation
        for logger in logging.Logger.manager.loggerDict.values():
            if isinstance(logger, SmartLogger):
                logger.propagate = False

    @staticmethod
    def get_record():
        return SmartLogger.get_record_parts(timestamp = True,
                                     # level = True,
                                     # logger_name = True,
                                     relative_created = True,
                                     file_path = True,
                                     file_name = True,
                                     lineno = True,
                                     func_name = True,
                                     thread_id = True,
                                     thread_name = True,
                                     task_name = True,
                                     process_id = True,
                                     process_name = True,
                                     exc_info = True,
                                     stack_info = True,
                                     )

    @staticmethod
    def get_record_parts(
        *,
        timestamp: bool = False,
        # level: bool = False,
        # logger_name: bool = False,
        relative_created: bool = False,
        file_path: bool = False,
        file_name: bool = False,
        lineno: bool = False,
        func_name: bool = False,
        thread_id: bool = False,
        thread_name: bool = False,
        task_name: bool = False,
        process_id: bool = False,
        process_name: bool = False,
        exc_info: bool = False,
        stack_info: bool = False,
    ) -> RetrievedRecord:
        """
        Retrieve a strongly-typed snapshot of selected log-record fields
        without emitting any log entry and without modifying any existing
        SmartLogger behavior.

        This method is intended as a thinking and debugging aid. It does not
        participate in the logging pipeline, does not create a LogRecord, and
        does not interact with handlers, formatters, or structured fields.

        Parameters (all keyword-only):
            timestamp        – Include an ISO-formatted timestamp (no 'T', millisecond precision).
            level            – Include the logger's numeric level.
            logger_name      – Include the logger's name.
            relative_created – Time (in seconds) since the logging system was initialized.
            file_path        – Full path of the caller's source file.
            file_name        – Basename of the caller's source file.
            lineno           – Line number of the caller.
            func_name        – Function name of the caller.
            thread_id        – Current thread identifier.
            thread_name      – Current thread name.
            task_name        – Current asyncio task name, if any.
            process_id       – Current process ID.
            process_name     – Current process name (best-effort, no external dependencies).
            exc_info         – Current exception info tuple, if any.
            stack_info       – Formatted stack trace of the current thread.

        Returns:
            RetrievedRecord – A dataclass instance containing only the fields
            explicitly requested. All other fields are set to None.

        Raises:
            ValueError – If no fields were requested.
            RuntimeError – If the logger is retired.

        Notes:
            • This method is intentionally isolated from the logging pipeline.
            • Structured fields and message text are not included.
            • Caller information is resolved using SmartLogger's existing
              caller-detection logic, without modifying it.
        """

        def _get_caller_frame():
            frame = inspect.currentframe()
            if frame is None:
                return None

            # Step 1: move to the caller of get_record_parts()
            caller = frame.f_back

            # Step 2: detect if the caller is SmartLogger.get_record
            skip = 2
            if caller:
                caller_self = caller.f_locals.get("self")
                if caller.f_code.co_name == "get_record" and isinstance(caller_self, SmartLogger):
                    skip = 3

            # Step 3: walk up the stack
            for _ in range(skip):
                if caller:
                    caller = caller.f_back

            return caller

        # ---------------------------------------------------------------
        # 1. Validate that at least one field is requested
        # ---------------------------------------------------------------
        if not any([
            # timestamp, level, logger_name, relative_created,
            timestamp, relative_created,
            file_path, file_name, lineno, func_name,
            thread_id, thread_name, task_name,
            process_id, process_name,
            exc_info, stack_info
        ]):
            raise ValueError("get_record() requires at least one field to be True.")

        # ---------------------------------------------------------------
        # 2. Capture timestamp (independent of logging pipeline)
        # ---------------------------------------------------------------
        now = time.time()

        # ---------------------------------------------------------------
        # 3. Capture caller info using existing SmartLogger helper
        # ---------------------------------------------------------------
        # noinspection PyBroadException
        try:
            # noinspection PyNoneFunctionAssignment,PyTupleAssignmentBalance
            # fn, lno, func = self._find_caller(stacklevel = 3)
            caller_frame = _get_caller_frame()

            if caller_frame:
                fn = caller_frame.f_code.co_filename
                lno = caller_frame.f_lineno
                func = caller_frame.f_code.co_name
            else:
                fn = lno = func = None

        except Exception:
            fn, lno, func = None, None, None

        # ---------------------------------------------------------------
        # 4. Capture thread/process/task info
        # ---------------------------------------------------------------
        thread_obj = threading.current_thread()
        pid = os.getpid()

        # Task name (asyncio) — optional, safe fallback
        # noinspection PyBroadException
        try:
            import asyncio
            task = asyncio.current_task()
            task_name_val = task.get_name() if task else None
        except Exception:
            task_name_val = None

        # ---------------------------------------------------------------
        # 5. Capture diagnostics
        # ---------------------------------------------------------------
        exc_val = sys.exc_info() if exc_info else None
        stack_val = "".join(traceback.format_stack()) if stack_info else None

        # ---------------------------------------------------------------
        # 6. Build the RetrievedRecord dataclass
        # ---------------------------------------------------------------
        rec = RetrievedRecord()

        if timestamp:
            dt = datetime.fromtimestamp(now)
            rec.timestamp = dt.isoformat(timespec="milliseconds").replace("T", " ")

        # if level:
        #     rec.level = logging.getLevelName(self.level)
        #
        # if logger_name:
        #     rec.logger_name = self.name

        if relative_created:
            # noinspection PyUnresolvedReferences,PyProtectedMember
            rec.relative_created = now - logging._startTime
            if rec.relative_created < 0:
                rec.relative_created = 0

        if file_path:
            rec.file_path = fn

        if file_name:
            rec.file_name = os.path.basename(fn) if fn else None

        if lineno:
            rec.lineno = lno

        if func_name:
            rec.func_name = func

        if thread_id:
            rec.thread_id = thread_obj.ident

        if thread_name:
            rec.thread_name = thread_obj.name

        if task_name:
            rec.task_name = task_name_val

        if process_id:
            rec.process_id = pid

        if process_name:
            rec.process_name = SmartLogger.__get_process_name()

        if exc_info:
            exc_type, exc_value, exc_tb = exc_val
            rec.exc_info = {
                "exc_parts": {
                    "err_type_name": None if exc_type  is None else exc_type.__name__,
                    "error_text":    None if exc_value is None else exc_value.__str__(),
                    "stack_trace":   None if exc_tb    is None else ''.join(traceback.format_tb(exc_tb)),
                },
                "full_trace_text":   None if exc_type  is None else ''.join(traceback.format_exception(exc_type, exc_value, exc_tb)),
            }

        if stack_info:
            rec.stack_info = stack_val

        return rec

    @staticmethod
    def __get_process_name() -> str | None:
        # Windows
        # noinspection PyBroadException
        try:
            exe = os.path.basename(sys.executable)
            if exe:
                return exe
        except Exception:
            pass

        # Linux / WSL / Android
        # noinspection PyBroadException
        try:
            with open("/proc/self/comm", "r") as f:
                name = f.read().strip()
                if name:
                    return name
        except Exception:
            pass

        # macOS / BSD / fallback
        # noinspection PyBroadException
        try:
            arg0 = os.path.basename(sys.argv[0])
            if arg0:
                return arg0
        except Exception:
            pass

        return None


# # ======================================================================
# #  REGISTER BUILT-IN LEVELS
# # ======================================================================
# LEVELS.register("TRACE", TRACE,
#     LevelStyle(fg = CPrint.FG.SOFT_PURPLE, intensity = CPrint.Intensity.NORMAL),
# )
# LEVELS.register("DEBUG", logging.DEBUG,
#     LevelStyle(fg = CPrint.FG.CYAN, intensity = CPrint.Intensity.NORMAL),
# )
# LEVELS.register("INFO", logging.INFO,
#     LevelStyle(fg = CPrint.FG.NEON_GREEN, intensity = CPrint.Intensity.NORMAL),
# )
# LEVELS.register("WARNING", logging.WARNING,
#     LevelStyle(fg = CPrint.FG.NEON_YELLOW, intensity = CPrint.Intensity.NORMAL),
# )
# LEVELS.register("ERROR", logging.ERROR,
#     LevelStyle(fg = CPrint.FG.NEON_RED, intensity = CPrint.Intensity.BOLD),
# )
# LEVELS.register("CRITICAL", logging.CRITICAL,
#     LevelStyle(fg = CPrint.FG.NEON_YELLOW, bg = CPrint.BG.NEON_RED, intensity = CPrint.Intensity.BOLD,
#                styles = (CPrint.Style.UNDERLINE,),
#     ),
# )


# ======================================================================
#  PROTOCOL FOR TYPE CHECKING
# ======================================================================
class SmartLoggerProtocol(Protocol):
    def trace(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None: ...


# ======================================================================
#  Global stdout logger (lazy initialization)
# ======================================================================
__stdout_logger = None
__stdout_lock = threading.Lock()


def __get_stdout_logger() -> "SmartLogger":
    """
    Internal helper that creates a dedicated SmartLogger instance
    for stdout redirection. It has exactly one console handler and
    does not propagate or write to files.
    """
    global __stdout_logger

    if __stdout_logger is not None:
        return __stdout_logger

    with __stdout_lock:
        if __stdout_logger is None:
            lg = SmartLogger("_stdout", level=logging.INFO)
            lg.add_console(level=logging.INFO)
            lg.propagate = False
            __stdout_logger = lg

    return __stdout_logger


def stdout(*args, sep=" ", end="\n"):
    """
    A SmartLogger‑synchronized replacement for print().

    Behaves exactly like print(), including handling of sep and end,
    but routes output through SmartLogger.raw() so console output is
    perfectly synchronized with all SmartLogger log messages.

    Auto-flushes to guarantee ordering with log messages.
    """
    lg = __get_stdout_logger()

    # Capture print() output exactly as Python formats it
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        print(*args, sep=sep, end=end)

    text = buffer.getvalue()

    # Forward the fully formatted text to SmartLogger.raw()
    # raw() already flushes, and we intentionally set end=""
    lg.raw(text, end="")
