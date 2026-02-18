# 🧠 Core Concepts

SmartLogger builds on Python’s `logging` module but introduces a structured, modernized architecture.</br>
Understanding these core concepts will help you use the framework effectively and confidently.

---

## 🔹 1. Global Initialization

SmartLogger replaces Python’s root logger with a SmartLogger root.
This ensures consistent behavior across all loggers in the application.

```python
levels = SmartLogger.levels()
SmartLogger.initialize_smartlogger(level = levels["INFO"])
```

Initialization must happen **once**, at the very beginning of your application.

---

## 🔹 2. Logger Creation

SmartLogger provides a clean, predictable way to create loggers:

```python
logger = SmartLogger.get("myapp.module", level = levels["DEBUG"])
```

Features:
- Ensures the logger is a `SmartLogger` instance
- Removes stale loggers with the same name
- Applies the specified level
- Does **not** inherit handlers from parents unless you add them

---

## 🔹 3. Handlers

Each logger may have:
- **Zero or One console handler**
- **Zero or more file handlers**</br>
Note that without handlers, a logger doesn't do anything

Handlers are attached explicitly:

```python
logger.add_console(level = levels["INFO"])
logger.add_file(log_dir = "logs", logfile_name = "app.log")
```
SmartLogger does **not** propagate logs upward unless auditing is enabled.

---

## 🔹 4. Structured Formatting

SmartLogger uses `LogRecordDetails` to control:

- Timestamp format
- Separator character
- Optional fields (file, line, thread, process, etc.)
- Field ordering
- Whether to colorize all fields or only level & message

### Example:

```python
details = LogRecordDetails(
    optional_record_fields = OptionalRecordFields(
        logger_name = True,
        lineno = True,
    ),
    message_parts_order = [
        # [timestamp] is always the *first* field in a log entry and is never specified here
        "level",        # when optional fields are specified, the position of [level] must be given here
        "logger_name",
        "lineno",
        # [message] is always the *first* field in a log entry and is never specified here
    ],
)
```

This produces consistent, readable, structured logs.

---

## 🔹 5. Color & Gradient Output

SmartLogger integrates a powerful ANSI color engine:

- Solid colors
- 256‑color gradients
- Foreground + background gradients
- Named palettes
- Palette blending

Example:

```python
from smartlogger import CPrint, GradientPalette

logger.raw(CPrint.gradient("Hello", fg_codes = GradientPalette.RAINBOW))
```

---

## 🔹 6. Rotation Logic

SmartLogger supports:

- **Size‑based rotation**
- **Time‑based rotation** (second, minute, hour, daily, weekly)
- **Hybrid rotation** (size OR time)
- **Retention policies** (delete old rotated files)
- **PID and timestamp suffixing**
- **Cross‑process‑safe rotation**

Example:

```python
rotation = RotationLogic(
    maxBytes = 50_000,
    when = When.SECOND,
    interval = 1,
    backupCount = 10,
)
```

---

## 🔹 7. Global Auditing

Auditing duplicates **all log records from all SmartLogger instances** into a single audit file.

```python
SmartLogger.audit_everything(
    log_dir="audit",
    logfile_name = "audit.log",
)
```

Auditing:

- Enables propagation on all loggers
- Uses `AuditFormatter`
- Can use rotation and retention
- Can be disabled at any time

---

## 🔹 8. Dynamic Log Levels

SmartLogger allows registering new levels at runtime:

```python
SmartLogger.register_level("NOTICE", 25)
logger.notice("Hello")
```

Dynamic levels automatically become methods via `__getattr__`.</br>
This prevents the IED from indicating warnings regarding dynamically added level-methods being unknown SmartLogger members.

---

## 🔹 9. Logger Lifecycle

SmartLogger supports:

### ✔ Retiring a logger
Closes handlers and marks the logger unusable.

```python
logger.retire()
```

### ✔ Destroying a logger
Removes it from the logging system entirely.

```python
logger.destroy()
```

This allows clean recreation of loggers with the same name.

---

## 🔹 10. Hierarchy & Inheritance

Logger names define hierarchy:

```
myapp
myapp.api
myapp.api.users
```

Rules:

- A logger with level `NOTSET` inherits from its parent
- Handlers **do not** propagate unless auditing is enabled
- Each logger manages its own handlers independently

---

# 🧩 Summary

SmartLogger’s architecture is built around:

- **Explicit initialization**
- **Explicit handler attachment**
- **Structured formatting**
- **Color‑aware output**
- **Safe rotation and retention**
- **Optional global auditing**
- **Dynamic log levels**
- **Predictable hierarchy behavior**

These concepts form the foundation for all features demonstrated in the examples.
```
