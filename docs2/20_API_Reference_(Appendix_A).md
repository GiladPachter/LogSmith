# Appendix A — API Reference  
This appendix provides a complete reference for all public classes, methods, configuration objects, and constants in LogSmith. It is designed as a quick lookup for developers who already understand the concepts covered in previous chapters.

---

# 🧠 SmartLogger  
The primary synchronous logger.

## Constructor
```python
SmartLogger(name: str, level: int = NOTSET)
```

## Core Methods
- `add_console()` — attach console handler
- `remove_console(...)` — remove the console handler
- `add_file(...)` — attach file handler  
- `remove_file_handler(...)` — remove a file handler by file name and directory
- `handler_info` — metadata of all logger's handlers
- `handler_info_json` — a json string representing handler_info (handler_info is not serializable)
- `console_handler`
- `file_handlers`
- `output_targets` — specified where all logger's handlers output logs
- `retire()` — disable logger, close handlers
- `destroy()` — remove logger entirely

## Logging Methods
- `trace(msg, **fields)`  
- `debug(msg, **fields)`  
- `info(msg, **fields)`  
- `warning(msg, **fields)`  
- `error(msg, **fields)`  
- `critical(msg, **fields)`  
- `raw(text)` — unformatted output  

## Static Methods
- `levels()` — a dictionary specifying all log levels
- `register_level(...)` — add dynamic logging level at runtime
- `apply_color_theme(...)` — change color and style of the built-in log levels
- `audit_everything()` — audit all loggers to one "root" superset log
- `terminate_auditing()` — stop auditing
- `get_record()` — get all log record metadata fields

## Properties
- `name` — logger's name
- `level` — logger's log level

Dynamic levels automatically add new methods.

---

# AsyncSmartLogger  
Async version of SmartLogger.

The differences are as follows:

## Async Logging Methods
- `await a_trace(msg, **fields)`  
- `await a_debug(msg, **fields)`  
- `await a_info(msg, **fields)`  
- `await a_warning(msg, **fields)`  
- `await a_error(msg, **fields)`  
- `await a_critical(msg, **fields)`  
- `await a_exception(msg, **fields)`  
- `await a_stdout(text)` — synchronized printing  

## Methods
- `queue_size` — current size of entries pending in the queue for logging
- `enable_profiling(...)` — track performance bottlenecks  
- `get_profiling_details(...)` — get profiling details  
- `await flush()` — flush queue  

## Static methods
- `messages_processed()` — total async log entries processed  
- `queue_size` — current size of entries pending in the queue for logging

---

# Handlers

## Console Handler
Created via:
```python
logger.add_console(
    level=None,
    output_mode=OutputMode.COLOR,
    log_record_details=None,
)
```

## File Handler
Created via:
```python
logger.add_file(
    log_dir: str,
    logfile_name: str,
    level=None,
    output_mode=OutputMode.PLAIN,
    rotation_logic=None,
    log_record_details=None,
    do_not_sanitize_colors_from_string=False,
)
```

Properties:
- `path`  
- `rotation_logic`  
- `retention`  
- `output_mode`  
- `formatter`  

---

# LogRecordDetails  
Controls structured formatting.

```python
LogRecordDetails(
    datefmt="%Y-%m-%d %H:%M:%S",
    separator="•",
    optional_record_fields=OptionalRecordFields(...),
    message_parts_order=[...],
    color_all_log_record_fields=False,
)
```

---

# OptionalRecordFields  
Enable/disable metadata fields.

```python
OptionalRecordFields(
    logger_name=False,
    file_name=False,
    lineno=False,
    func_name=False,
    thread_id=False,
    process_id=False,
    module_name=False,
    pathname=False,
)
```

---

# RotationLogic  
Controls rotation behavior.

```python
RotationLogic(
    maxBytes=None,
    when=None,
    interval=1,
    timestamp=None,
    backupCount=0,
    expiration_rule=None,
)
```

---

# RotationTimestamp  
Defines daily/weekly rotation anchors.

```python
RotationTimestamp(hour=0, minute=0, second=0)
```

---

# ExpirationRule  
Defines retention policy.

```python
ExpirationRule(
    scale=ExpirationScale.Days,
    interval=7,
)
```

---

# OutputMode  
Enum for output formatting.

- `COLOR`  
- `PLAIN`  
- `JSON`  
- `NDJSON`  

---

# LevelStyle  
Defines color/style for a log level.

```python
LevelStyle(
    fg=None,
    bg=None,
    bold=False,
    dim=False,
    underline=False,
    italic=False,
    strike=False,
)
```

---

# CPrint  
ANSI color engine.

## Methods
- `colorize(text, fg=None, bg=None, bold=False, ...)`  
- `gradient(text, fg_codes, bg_codes=None)`  

## Color Constants
- `CPrint.FG.*`  
- `CPrint.BG.*`  

---

# GradientPalette  
Predefined palettes.

- `RAINBOW`  
- `FIRE`  
- `OCEAN`  
- `FOREST`  
- `SUNSET`  
- `PASTEL`  

Custom palette:

```python
GradientPalette([196, 202, 208])
```

---

# Auditing  
Global capture of all logs.

## Enable
```python
SmartLogger.audit_everything(
    log_dir="audit",
    logfile_name="audit.log",
    output_mode=OutputMode.NDJSON,
    rotation_logic=None,
)
```

Async version:

```python
AsyncSmartLogger.audit_everything(...)
```

## Disable
```python
SmartLogger.stop_auditing()
await AsyncSmartLogger.stop_auditing()
```

---

# Dynamic Levels  
Register new levels:

```python
SmartLogger.register_level("NOTICE", 25)
AsyncSmartLogger.register_level("SUCCESS", 35)
```

Automatically creates:

- new level constant  
- new logger method  
- theme integration  

---

# Global Utilities

## Get Logger
```python
SmartLogger.get_logger(name)
AsyncSmartLogger.get_logger(name)
```

## Shutdown
```python
SmartLogger.shutdown()
await AsyncSmartLogger.shutdown()
```

---

# Summary  
This appendix provides a complete reference for:

- SmartLogger and AsyncSmartLogger  
- handlers  
- formatting  
- rotation  
- themes  
- auditing  
- dynamic levels  
- global utilities  

The next appendix covers **Appendix B: Glossary**, defining all terminology used throughout the documentation.
