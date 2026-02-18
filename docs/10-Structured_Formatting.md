# 🧱 Structured Formatting

SmartLogger provides a powerful, declarative formatting system built around two core classes:

- **`LogRecordDetails`** — controls *what* appears in each log entry
- **`OptionalRecordFields`** — controls *which metadata fields* are included

This system replaces fragile format strings with a clean, structured configuration model.

---

# 🔹 LogRecordDetails

`LogRecordDetails` defines:

- timestamp format
- separator character
- optional metadata fields
- ordering of fields
- whether to colorize all fields or only level/message

Example:

```python
from smartlogger import LogRecordDetails, OptionalRecordFields
details = LogRecordDetails(
    datefmt = "%Y-%m-%d %H:%M:%S.%3f",
    separator = "•",
    optional_record_fields = OptionalRecordFields(
        logger_name = True,
        file_name = True,
        lineno = True,
    ),
    message_parts_order = [
        "level",
        "logger_name",
        "file_name",
        "lineno",
    ],
)
```

Attaching LogRecordDetails to a handler:

```python
logger.add_console(log_record_details = details)
```

---

# 🔹 OptionalRecordFields

This class controls which metadata fields appear between the timestamp and the message.

Available fields include:

- `logger_name`
- `file_path`
- `file_name`
- `lineno`
- `func_name`
- `thread_id`, `thread_name`
- `process_id`, `process_name`
- `task_name`
- `relative_created`
- diagnostics: `exc_info`, `stack_info`

Example:

```python
OptionalRecordFields(
    func_name = True,
    lineno = True,
    thread_id = True,
)
```

---

# 🔹 Message Parts Ordering

`message_parts_order` defines the exact order of inline fields.

Rules:
- `timestamp` is always first and is not to be specified in fields order
- `message` is always last and is not to be specified in fields order
- `level` must appear exactly once (for positioning vs. the selected optional fields)
- only enabled fields may appear (other than `level`)
- diagnostics (`exc_info`, `stack_info`) must **not** appear here

Example:

```python
message_parts_order = [
    "level",
    "file_path",
    "lineno",
]
```

---

# 🔹 Simple Mode vs Strict Mode

## ✔ Simple Mode
If `optional_record_fields == None`, SmartLogger uses:

```
timestamp • LEVEL • message
```

This is ideal for quick setups.

---

## ✔ Strict Mode
If optional fields are provided, SmartLogger enforces:
- validation of enabled / disabled fields
- validation of field ordering
- validation of legal separator
- validation of date format (including `%1f`–`%6f` fractional seconds)

Strict mode ensures consistent, predictable formatting across all handlers.

---

# 🔹 Diagnostics: exc_info and stack_info

SmartLogger supports structured diagnostics:

```python
try:
    1 / 0
except ZeroDivisionError:
    logger.error("An error occurred", exc_info = True)
```

Or:

```python
logger.debug("Debug with stack info", stack_info = True)
```

Diagnostics appear **after** the main log entry.

---

# 🔹 Extras (Named Arguments)

SmartLogger supports structured extras:

```python
logger.info("User login", user = "Gilad", action = "login")
```

These appear as a JSON‑like dictionary at the end of the log line:

```
{ user = 'Gilad', action = 'login' }
```

Extras are extracted automatically and merged with any `fields = {}` dict.

---

# 🔹 Color Behavior

By default:

- only the **level** and **message** are colorized
- metadata fields are dimmed

To colorize the entire entry:

```python
LogRecordDetails(color_all_log_record_fields = True)
```

This is ideal for high‑visibility console output.

---

# 🔹 Timestamp Formatting

SmartLogger supports fractional seconds using `%1f` through `%6f`:

```python
datefmt = "%Y-%m-%d %H:%M:%S.%3f"
```

This produces millisecond precision.

Invalid formats (e.g., `%7f`) raise a clear error.

---

# 🧩 Summary

SmartLogger’s structured formatting system provides:

- declarative configuration
- strict validation
- flexible metadata fields
- customizable ordering
- color‑aware output
- structured extras
- clean diagnostics

This makes log output consistent, readable, and ideal for both humans and machines.
```
