# 🖥️ Console Logging

LogSmith provides a powerful, color‑aware console handler designed for clarity, structure, and expressiveness.</br>
Console output uses ANSI colors, level‑aware styling, and optional structured metadata.

---

## 🔹 Adding a Console Handler

Each logger may have **one** console handler:

```python
logger.add_console(level = levels["INFO"])
```

This defines a console handler configured with the default `LogRecordDetails`.

---

## 🔹 Basic Console Output

```python
logger.trace("trace message")
logger.debug("debug message")
logger.info("info message")
logger.warning("warning message")
logger.error("error message")
logger.critical("critical message")
```

Each level is color‑coded according to its `LevelStyle`.

---

## 🔹 Customizing Console Formatting

Use `LogRecordDetails` to control:

- timestamp format
- separator
- optional fields
- field ordering
- whether to colorize all fields or just level & message

Example:

```python
details = LogRecordDetails(
    optional_record_fields = OptionalRecordFields(
        logger_name = True,
        file_name = True,
        lineno = True,
        func_name = True,
    ),
    message_parts_order = [
        "logger_name",
        "file_name",
        "lineno",
        "level",
        "func_name",
    ],
    color_all_log_record_fields = True,
)

logger.add_console(level = levels["TRACE"], log_record_details = details)
```

This produces a fully colorized, structured log entry.

---

## 🔹 Named Arguments (Structured Fields)

LogSmith supports structured fields via named arguments:

```python
logger.info("User login:", user = "Gilad", password = "Aa123456")
```

These appear as a JSON‑like dictionary at the end of the log line.</br>
Like this:</br>
2026-02-15 01:08:46.035 • INFO     • User login: **{username = 'Gilad', password = 'Aa123456'}**


---

## 🔹 Raw Console Output

Use `logger.raw()` to write only the message part of a log record to the console:

```python
logger.raw("This is raw text")
logger.raw(CPrint.colorize("Colored raw text", fg = CPrint.FG.BRIGHT_RED))
```

Raw output:

- bypasses formatting
- preserves ANSI colors
- is ideal for banners, headers, and gradient text

---

## 🔹 Gradient Output

LogSmith integrates seamlessly with the gradient engine:

```python
from LogSmith import CPrint, GradientPalette

logger.raw(CPrint.gradient("Rainbow!", fg_codes=GradientPalette.RAINBOW))
```

Gradients support:

- foreground
- background
- multi‑line vertical gradients
- auto‑stretching
- palette blending

---

## 🔹 Handler Introspection

You can inspect the handlers of a SmartLogger object:

```python
print(logger.handler_info)
```

This returns a clean, human‑readable dictionary.

---

# 🧩 Summary

Console logging in LogSmith provides:

- level‑aware color output
- structured metadata
- customizable formatting
- raw ANSI output
- gradient support
- clean handler introspection

This makes console logs expressive, readable, and ideal for both development and production.
