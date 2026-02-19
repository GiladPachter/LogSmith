# LogSmith/formatter.py

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from .colors import CPrint, Code
from .levels import LevelStyle
from .level_registry import LEVELS


# ================================================================
# OptionalRecordFields
# ================================================================

@dataclass
class OptionalRecordFields:
    """
    Optional LogRecord fields that may appear between timestamp and message.
    Mandatory fields (timestamp, level, message) are NOT included here.
    """
    relative_created: bool = False
    logger_name:      bool = False
    file_path:        bool = False
    file_name:        bool = False
    lineno:           bool = False
    func_name:        bool = False
    thread_id:        bool = False
    thread_name:      bool = False
    task_name:        bool = False
    process_id:       bool = False
    process_name:     bool = False

    # diagnostics
    exc_info:   bool = False
    stack_info: bool = False


# ================================================================
# LogRecordDetails
# ================================================================

@dataclass
class LogRecordDetails:
    """
    LogRecordDetails controls which metadata fields appear in formatted log
    messages produced by SmartLogger.

    It allows fine‑grained selection of record attributes such as:
        • Timestamp
        • Log level
        • Logger name
        • Source file and line number
        • Thread and process identifiers
        • Message text

    SmartLogger uses this configuration to build a consistent, structured
    formatter for console and file output.

    Parameters
    ----------
    datefmt : str, optional
        date formatting, with fractions between %1f ... %6f
    separator : str, optional
        single character separator between logged record fields
    optional_record_fields : OptionalRecordFields, optional
        additional record fields on top of timestamp, level and message
    message_parts_order : List[str], optional
        the order of optional fields in the log entry
        timestamp always comes first and is not to be specified
        message always comes last and is not to be specified
        level can come anywhere in between and must be positioned vs. the optional fields
    color_all_log_record_fields : bool, optional
        by default, only level and message are colored.
        this allows coloration of the entire entry

    Notes
    -----
    LogRecordDetails is designed to keep formatting declarative and readable.
    It avoids hard‑coding format strings throughout the codebase and ensures
    that all SmartLogger output remains consistent and easy to parse.
    """

    datefmt:   str | None = "%Y-%m-%d %H:%M:%S.%3f"
    separator: str | None = "•"

    optional_record_fields: OptionalRecordFields | None = None
    message_parts_order: Optional[List[str]] = None

    color_all_log_record_fields: bool = False

    def __post_init__(self) -> None:

        # ------------------------------------------------------------
        # Basic separator validation
        # ------------------------------------------------------------
        if not isinstance(self.separator, str) or len(self.separator) != 1:
            raise ValueError("separator must be a single character")
        if self.separator.isalnum() or self.separator in "{}[]()<>":
            raise ValueError("separator must be non-alphanumeric and non-bracket")

        # ------------------------------------------------------------
        # Case A: optional_record_fields is None (simple mode)
        # ------------------------------------------------------------
        if self.optional_record_fields is None:
            if self.message_parts_order is not None:
                raise ValueError("message_parts_order must be None when optional_record_fields is None")
            if self.color_all_log_record_fields:
                raise ValueError("color_all_log_record_fields must be False when optional_record_fields is None")
            return

        # ------------------------------------------------------------
        # Case B: optional_record_fields is provided (strict mode)
        # ------------------------------------------------------------
        orf = self.optional_record_fields

        # Inline optional fields (diagnostics excluded)
        inline_fields = [
            f for f in vars(orf).keys()
            if f not in ("exc_info", "stack_info")
        ]

        inline_enabled = any(getattr(orf, f) for f in inline_fields)
        diagnostics_enabled = orf.exc_info or orf.stack_info

        # Case: only diagnostics enabled → message_parts_order must be None
        if diagnostics_enabled and not inline_enabled:
            if self.message_parts_order is not None:
                raise ValueError("message_parts_order must be None when only diagnostics fields are enabled")
            return

        # Case: inline fields enabled → message_parts_order required
        if not inline_enabled:
            raise ValueError("At least one inline optional field must be True when optional_record_fields is provided")

        if self.message_parts_order is None:
            raise ValueError("message_parts_order must be provided when inline optional fields are enabled")

        mpo = self.message_parts_order

        # ------------------------------------------------------------
        # timestamp and message must NOT appear
        # ------------------------------------------------------------
        forbidden = {"timestamp", "message"}
        if any(p in forbidden for p in mpo):
            raise ValueError("timestamp and message must NOT appear in message_parts_order")

        # ------------------------------------------------------------
        # level must appear exactly once
        # ------------------------------------------------------------
        if mpo.count("level") != 1:
            raise ValueError("message_parts_order must contain 'level' exactly once")

        # ------------------------------------------------------------
        # Optional inline fields must match message_parts_order exactly
        # ------------------------------------------------------------
        for field_name in inline_fields:
            enabled = getattr(orf, field_name)

            if enabled:
                if mpo.count(field_name) != 1:
                    raise ValueError(f"Optional field '{field_name}' is True but not present exactly once in message_parts_order")
            else:
                if field_name in mpo:
                    raise ValueError(f"Optional field '{field_name}' is False but appears in message_parts_order")

        # ------------------------------------------------------------
        # Diagnostics must NOT appear in message_parts_order
        # ------------------------------------------------------------
        if "exc_info" in mpo or "stack_info" in mpo:
            raise ValueError("exc_info and stack_info must not appear in message_parts_order")

        # ------------------------------------------------------------
        # Allowed message parts
        # ------------------------------------------------------------
        allowed = set(inline_fields) | {"level"}
        for part in mpo:
            if part not in allowed:
                raise ValueError(
                    f"Invalid message part: {part!r}. "
                    f"Allowed parts are OptionalRecordFields attributes or 'level'."
                )


# ================================================================
# Timestamp formatting
# ================================================================

def _format_timestamp(record: logging.LogRecord, datefmt: str | None) -> str:
    if datefmt is None:
        return datetime.fromtimestamp(record.created).isoformat(sep=" ", timespec="seconds")

    import re
    base = datetime.fromtimestamp(record.created)

    match = re.search(r"%([1-6])f", datefmt)
    if match:
        digits = int(match.group(1))
        placeholder = "__FRACTIONAL_SECONDS__"
        normalized = re.sub(r"%[1-6]f", placeholder, datefmt)
        rendered = base.strftime(normalized)
        micros = f"{base.microsecond:06d}"[:digits]
        return rendered.replace(placeholder, micros)

    invalid = re.search(r"%([0,7-9])f", datefmt)
    if invalid:
        raise ValueError(
            f"Invalid fractional seconds directive '{invalid.group(0)}'. "
            "Only %1f through %6f are supported."
        )

    if "%f" in datefmt:
        return base.strftime(datefmt)

    return base.strftime(datefmt)


# ================================================================
# Extras extraction
# ================================================================

def _extract_extras(record: logging.LogRecord) -> Dict[str, Any]:
    standard = {
        "name", "msg", "args", "levelname", "levelno",
        "pathname", "filename", "module", "exc_info",
        "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread",
        "threadName", "processName", "process",
        "taskName", "task",
        "message", "asctime",
    }
    extras: Dict[str, Any] = {
        k: v for k, v in record.__dict__.items() if k not in standard
    }

    fields = extras.get("fields", {})
    if isinstance(fields, dict):
        extras = {k: v for k, v in extras.items() if k != "fields"}
        extras.update(fields)

    return extras


# ================================================================
# Plain formatter
# ================================================================

class StructuredPlainFormatter:
    """
    Plain (non-colored) formatter driven by LogRecordDetails.
    """

    def __init__(self, details: LogRecordDetails) -> None:
        if details is None:
            details = LogRecordDetails()
        self._details = details

    def format(self, record: logging.LogRecord) -> str:
        rf = self._details.optional_record_fields

        # SIMPLE MODE
        if rf is None:
            parts = [
                _format_timestamp(record, self._details.datefmt),
                record.levelname,
                record.getMessage(),
            ]
            line = f" {self._details.separator} ".join(parts)

            extras = _extract_extras(record)
            if extras:
                kv = " ".join(f"{k}={v!r}" for k, v in extras.items())
                line = f"{line} {kv}"

            return line

        # STRICT MODE
        # noinspection PyListCreation
        parts = []

        # Always first
        parts.append(_format_timestamp(record, self._details.datefmt))

        if self._details.message_parts_order is None:
            # diagnostics-only mode (no inline fields)
            parts.append(record.levelname)
        else:
            # Inline fields
            for part in self._details.message_parts_order:
                if part == "level":
                    parts.append(record.levelname)
                elif part == "relative_created" and rf.relative_created:
                    parts.append(str(int(record.relativeCreated)))
                elif part == "logger_name" and rf.logger_name:
                    parts.append(f"LOGGER={record.name}")
                elif part == "file_path" and rf.file_path:
                    parts.append(record.pathname)
                elif part == "file_name" and rf.file_name:
                    parts.append(record.filename)
                elif part == "lineno" and rf.lineno:
                    parts.append("L=" + str(record.lineno))
                elif part == "func_name" and rf.func_name:
                    parts.append(record.funcName)
                elif part == "thread_id" and rf.thread_id:
                    parts.append("th=" + str(record.thread))
                elif part == "thread_name" and rf.thread_name:
                    parts.append(record.threadName)
                elif part == "task_name" and rf.task_name and hasattr(record, "taskName"):
                    parts.append(getattr(record, "taskName"))
                elif part == "process_id" and rf.process_id:
                    parts.append("P=" + str(record.process))
                elif part == "process_name" and rf.process_name:
                    parts.append(record.processName)

        # Always last
        parts.append(record.getMessage())

        line = f" {self._details.separator} ".join(parts)

        extras = _extract_extras(record)
        if extras:
            kv = " ".join(f"{k}={v!r}" for k, v in extras.items())
            line = f"{line} {kv}"

        if record.exc_info and rf.exc_info:
            line += "\n" + logging.Formatter().formatException(record.exc_info)
        if record.stack_info and rf.stack_info:
            line += "\n" + str(record.stack_info)

        return line


# ================================================================
# Color formatter (table-driven)
# ================================================================

Renderer = Callable[[logging.LogRecord], str]

class StructuredColorFormatter:
    """
    Colored formatter driven by LogRecordDetails.
    Table-driven field rendering.
    JSON extras.
    No color bleed.
    """

    def __init__(
        self,
        details:       LogRecordDetails,
        *,
        key_fg:        Code | None = CPrint.FG.WHITE,
        key_intensity: Code | None = CPrint.Intensity.BOLD,
        value_fg:      Code | None = CPrint.FG.DIM_GREY,
    ) -> None:
        if details is None:
            details = LogRecordDetails()
        self._details       = details
        self._key_fg        = key_fg
        self._key_intensity = key_intensity
        self._value_fg      = value_fg
        self._current_style: LevelStyle | None = None

        self.FIELD_RENDERERS: dict[str, Renderer] = {
            "relative_created": self.render_relative_created,
            "level":            self.render_level,
            "logger_name":      self.render_logger_name,
            "file_path":        self.render_file_path,
            "file_name":        self.render_file_name,
            "lineno":           self.render_lineno,
            "func_name":        self.render_func_name,
            "thread_id":        self.render_thread_id,
            "thread_name":      self.render_thread_name,
            "task_name":        self.render_task_name,
            "process_id":       self.render_process_id,
            "process_name":     self.render_process_name,
        }

    # ------------------------------------------------------------
    # Styling helpers
    # ------------------------------------------------------------
    @staticmethod
    def dim(text: str) -> str:
        return CPrint.colorize(
            text,
            fg=CPrint.FG.CONSOLE_DEFAULT,
            intensity=CPrint.Intensity.DIM,
        )

    @staticmethod
    def apply_level(text: str, style: LevelStyle | None) -> str:
        if not style:
            return text
        return CPrint.colorize(
            text,
            fg=style.fg,
            bg=style.bg,
            intensity=style.intensity,
            styles=style.styles,
        )

    def style_meta(self, text: str, style: LevelStyle | None) -> str:
        if self._details.color_all_log_record_fields:
            return self.apply_level(text, style)
        return self.dim(text)

    # ------------------------------------------------------------
    # Field renderers
    # ------------------------------------------------------------
    def render_timestamp(self, rec):
        ts = _format_timestamp(rec, self._details.datefmt)
        return self.style_meta(ts, self._current_style)

    def render_relative_created(self, rec):
        return self.style_meta(str(int(rec.relativeCreated)), self._current_style)

    def render_level(self, rec):
        return self.apply_level(rec.levelname.ljust(8), self._current_style)

    def render_logger_name(self, rec):
        return self.style_meta(f"LOGGER={rec.name}", self._current_style)

    def render_file_path(self, rec):
        return self.style_meta(rec.pathname, self._current_style)

    def render_file_name(self, rec):
        return self.style_meta(rec.filename, self._current_style)

    def render_lineno(self, rec):
        return self.style_meta("L=" + str(rec.lineno), self._current_style)

    def render_func_name(self, rec):
        return self.style_meta(rec.funcName, self._current_style)

    def render_thread_id(self, rec):
        return self.style_meta("t=" + str(rec.thread), self._current_style)

    def render_thread_name(self, rec):
        return self.style_meta(rec.threadName, self._current_style)

    def render_task_name(self, rec):
        return self.style_meta(getattr(rec, "taskName"), self._current_style)

    def render_process_id(self, rec):
        return self.style_meta("P=" + str(rec.process), self._current_style)

    def render_process_name(self, rec):
        return self.style_meta(rec.processName, self._current_style)

    def render_message(self, rec):
        return self.apply_level(rec.getMessage(), self._current_style)

    # ------------------------------------------------------------
    # Extras renderer
    # ------------------------------------------------------------
    @staticmethod
    def render_extras_colored(named_arguments: dict) -> str:
        parts = []
        for k, v in named_arguments.items():
            colored_key = CPrint.colorize(
                k,
                fg=CPrint.FG.BRIGHT_WHITE,
                intensity=CPrint.Intensity.BOLD,
            )
            colored_val = CPrint.colorize(
                repr(v),
                fg=CPrint.FG.BRIGHT_GREY,
            )
            parts.append(f"{colored_key} = {colored_val}")
        return f"{{{', '.join(parts)}}}"

    # ------------------------------------------------------------
    # Main format()
    # ------------------------------------------------------------
    def format(self, record: logging.LogRecord) -> str:
        rf = self._details.optional_record_fields

        level_entry = LEVELS.get(record.levelname)
        self._current_style = level_entry["style"] if level_entry else None

        if rf is None:  # SIMPLE MODE
            parts = [
                self.render_timestamp(record),
                self.render_level(record),
                self.render_message(record),
            ]
        else:   # STRICT MODE
            # timestamp is always first
            parts = [self.render_timestamp(record)]

            # Inline fields
            if self._details.message_parts_order:
                for part in self._details.message_parts_order:
                    renderer = self.FIELD_RENDERERS.get(part)
                    if renderer:
                        parts.append(renderer(record))
            else:
                # diagnostics-only mode → include level
                parts.append(self.render_level(record))

            # Always last
            parts.append(self.render_message(record))

        sep = CPrint.colorize(
            self._details.separator,
            fg=CPrint.FG.BRIGHT_WHITE,
            intensity=CPrint.Intensity.BOLD,
        )
        line = f" {sep} ".join(parts)

        extras = _extract_extras(record)
        if extras:
            line = f"{line} {self.render_extras_colored(extras)}"

        # Diagnostics
        if rf and record.exc_info and rf.exc_info:
            line += "\n { exc_info }\n" + logging.Formatter().formatException(record.exc_info)
        if rf and record.stack_info and rf.stack_info:
            line += "\n { stack_info }\n" + str(record.stack_info)

        return line


# ================================================================
# formatter for file handles that doesn't sanitize text coloration
# ================================================================

class PassthroughFormatter(logging.Formatter):
    """
    Formatter that preserves ANSI escape sequences and returns the raw message.
    Used for file handlers that intentionally allow colored output.
    """
    def format(self, record: logging.LogRecord) -> str:
        return record.getMessage()


class AuditFormatter(logging.Formatter):
    """
    Formatter for global auditing.
    Preserves ANSI escape sequences and formats log records using the
    provided LogRecordDetails, while prefixing each entry with the
    originating logger's name.
    """

    def __init__(self, details: LogRecordDetails):
        super().__init__()
        self.details = details
        self.structured = StructuredPlainFormatter(details)

    def format(self, record: logging.LogRecord) -> str:
        prefix = f"[{record.name}]: "
        return prefix + self.structured.format(record)
