# 📚 API Reference Overview

This section provides a high‑level overview of SmartLogger’s public API.

---

# 🏷️ Core Classes

## SmartLogger

- `SmartLogger.levels()`
- `SmartLogger.get(name, level)`
- 
- `logger.add_console(...)`
- `logger.add_file(...)`
- 
- `SmartLogger.register_level()`
- `SmartLogger.apply_color_theme(theme: dict[int, LevelStyle])`
- 
- `logger.retire()`
- `logger.destroy()`
- 
- `logger.handler_info`
- `logger.console_handler`
- `logger.file_handlers`
- 
- `SmartLogger.audit_everything(...)`
- `SmartLogger.terminate_auditing()`
- 
- `SmartLogger.get_record()`
- `SmartLogger.get_record_parts(...)`

---

# 🧱 Formatting

## LogRecordDetails

- `datefmt`
- `separator`
- `optional_record_fields`
- `message_parts_order`
- `color_all_log_record_fields`

## OptionalRecordFields

- `logger_name`
- `file_name`
- `file_path`
- `lineno`
- `func_name`
- `thread_id`, `thread_name`
- `process_id`, `process_name`
- `task_name`
- `relative_created`
-
- \# &nbsp; Optional, but separate from the log record structure 
- \# &nbsp; The following only manifest when explicitly set True in logging methods
- `exc_info` # separate from the log record structure
- `stack_info` # separate from the log record structure

---

# 🎨 Colors & Styles

## CPrint

- `colorize(text, fg, bg, intensity, styles)`
- `gradient(text, fg_codes, bg_codes, direction)`
- `reverse(text)`
- `strip_ansi(text)`
- `escape_ansi_for_display(text)`
- `escape_control_chars(text)`

Includes:

- `FG`, `BG`, `Intensity`, `Style`

---

# 🎭 Themes

Themes are dictionaries:

```
Dict[int, LevelStyle]
```

Built‑in:

- `THEME_LIGHT`
- `THEME_DARK`
- `THEME_NEON`
- `THEME_PASTEL`
- `THEME_FIRE`
- `THEME_OCEAN`

Apply a color theme to log levels in the console output:

```python
from smartlogger.themes import THEME_DARK

SmartLogger.apply_color_theme("dark", THEME_DARK)
```

---

# 🧩 Structured Fields

- named arguments
- `fields = {}`
- merged automatically
- formatted as `{ key = value, ... }`

---

# 🧯 Exceptions & Diagnostics

- `exc_info = True`
- `stack_info = True`

Diagnostics appear after the log entry.

---

# 📁 File Logging & Rotation

## RotationLogic

- `when`
- `interval`
- `timestamp`
- `maxBytes`
- `backupCount`
- `expiration_rule`
- `append_filename_pid`
- `append_filename_timestamp`

## When

- `SECOND`
- `MINUTE`
- `HOUR`
- 
- `MONDAY`
- `TUESDAY`
- `WEDNESDAY`
- `THURSDAY`
- `FRIDAY`
- `SATURDAY`
- `SUNDAY`
- `EVERYDAY`

---

# 🧵 Concurrency & Multi‑Process Safety

- advisory locks
- atomic renames
- safe rotation
- minimal contention
- builtin retention

---

# 🧩 Summary

This overview covers:

- core logger API
- formatting
- colors
- themes
- structured fields
- diagnostics
- rotation
- concurrency safety
