# 📁 File Logging

SmartLogger provides a robust, concurrency‑safe file handler with support for:

- size‑based rotation
- time‑based rotation
- hybrid rotation (size OR time)
- retention policies
- PID and timestamp suffixing
- ANSI‑aware formatting (sanitize or preserve colors)

File handlers are added explicitly to each logger.

---

## 🔹 Adding a File Handler

```python
logger.add_file(
    log_dir = "logs",
    logfile_name = "app.log",
    level = levels["INFO"],
)
```

This creates:

```
logs/app.log
```

If the directory does not exist, SmartLogger creates it automatically.

---

## 🔹 Using Rotation Logic

Rotation is controlled by `RotationLogic`, which supports:

### ✔ Size‑based rotation
```python
RotationLogic(maxBytes = 50_000, backupCount = 5)
```

### ✔ Time‑based rotation
```python
RotationLogic(when = When.SECOND, interval = 1)
```

### ✔ Hybrid rotation
```python
RotationLogic(maxBytes = 50_000, when = When.SECOND, interval = 1)
```

Rotation triggers when **either** condition is met.

---

## 🔹 Retention Policies (Expiration Rules)

SmartLogger can automatically delete old rotated files:

```python
from smartlogger import ExpirationRule, ExpirationScale

rotation = RotationLogic(
    when = When.SECOND,
    interval = 1,
    backupCount = 10,
    expiration_rule = ExpirationRule(
        scale = ExpirationScale.Seconds,
        interval = 5,   # delete rotated files older than 5 seconds
    ),
)
```

Retention works independently of rotation triggers.

---

## 🔹 ANSI Sanitization (Color in Files)

By default, SmartLogger **removes ANSI escape sequences** when writing to files.

To preserve colors:

```python
logger.add_file(
    log_dir = "logs",
    logfile_name = "colored.log",
    do_not_sanitize_colors_from_string = True,
)
```

This is ideal for:

- gradient banners
- color‑rich debugging output
- terminal‑friendly log viewers

---

## 🔹 Structured File Formatting

You can customize formatting with ease, without requiring familiarity with formatting syntax:

```python
details = LogRecordDetails(
    datefmt = "%Y-%m-%d %H:%M:%S",
    separator = "|",
    optional_record_fields = OptionalRecordFields(
        logger_name = True,
        process_id = True,
        thread_id = True,
    ),
    message_parts_order = [
        "logger_name",
        "process_id",
        "thread_id",
        "level",
    ],
)

logger.add_file(
    log_dir = "logs",
    logfile_name = "structured.log",
    log_record_details = details,
)
```

---

## 🔹 Concurrency‑Safe Rotation

SmartLogger’s file handler is:

- thread‑safe
- cross‑process‑safe
- atomic (uses `os.replace`)
- lock‑protected (`fcntl` on Unix, `msvcrt` on Windows)

This prevents corruption when multiple processes write to the same log file.

---

## 🔹 Handler Introspection

You can inspect file handlers:

```python
print(logger.file_handlers)
```

Each entry includes:

- file path
- rotation settings
- retention settings
- sanitization mode

---

# 🧩 Summary

File logging in SmartLogger provides:

- safe, reliable rotation
- flexible retention
- structured formatting
- optional ANSI preservation
- concurrency‑safe writes
- clean handler introspection

This makes SmartLogger suitable for production‑grade logging in multi‑threaded and multi‑process environments.
