# 📝 File Logging  
LogSmith’s file logging system is built for real‑world workloads: multi‑threaded apps, multi‑process services, long‑running daemons, ingestion pipelines, and anything that needs safe, predictable log rotation. This chapter covers file handlers, rotation, retention, ANSI sanitization, and concurrency guarantees.

---

## 🔹 Adding a File Handler  
File handlers are explicit — LogSmith never writes to files unless you tell it to.

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

If the directory doesn’t exist, LogSmith creates it.

A logger may have **any number of file handlers**, each with its own formatting and rotation rules.

---

## 🔹 Output Modes for File Handlers  
File handlers support all output modes:

- **PLAIN** — structured text, no color  
- **COLOR** — structured text with ANSI (sanitized by default)  
- **JSON** — pretty JSON  
- **NDJSON** — compact JSON, one object per line  

Example:

```python
logger.add_file(
    log_dir = "logs",
    logfile_name = "events.ndjson",
    output_mode = OutputMode.NDJSON,
)
```

NDJSON is ideal for ingestion pipelines (ELK, Loki, BigQuery, etc.).

---

## 🔹 ANSI Sanitization (Color in Files)  
By default, LogSmith **removes ANSI escape sequences** when writing to files.  
This prevents corrupted logs and makes files safe for ingestion.

To preserve ANSI colors:

```python
logger.add_file(
    log_dir = "logs",
    logfile_name = "colored.log",
    do_not_sanitize_colors_from_string = True,
)
```

Use this only when you *intentionally* want colored log files (e.g., for demos or debugging).

---

## 🔹 Structured File Formatting  
File handlers use the same formatting engine as console handlers.

```python
details  =  LogRecordDetails(
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

This produces clean, structured, machine‑friendly logs.

---

## 🔹 Rotation Logic  
Rotation is controlled by a dedicated object:

```python
from LogSmith import RotationLogic, When

rotation = RotationLogic(
    maxBytes = 50_000,
    when = When.SECOND,
    interval = 1,
    backupCount = 5,
)
```

Attach it to a file handler:

```python
logger.add_file(
    log_dir = "logs",
    logfile_name = "rotating.log",
    rotation_logic = rotation,
)
```

Rotation triggers when **either** condition is met:

- file exceeds `maxBytes`  
- current time passes the next scheduled rotation moment  

This is hybrid rotation — size OR time.

---

## 🔹 Size‑Based Rotation  
Rotate when the file grows too large:

```python
RotationLogic(maxBytes = 100_000, backupCount = 10)
```

---

## 🔹 Time‑Based Rotation  
Rotate on a schedule:

```python
RotationLogic(
    when = When.SECOND,   # or MINUTE, HOUR, EVERYDAY, MONDAY, ...
    interval = 1,
)
```

Daily/weekly rotation uses a timestamp anchor:

```python
RotationLogic(
    when = When.EVERYDAY,
    timestamp = RotationTimestamp(hour = 0, minute = 0, second = 0),
)
```

---

## 🔹 Combined Rotation  
Use both size and time:

```python
RotationLogic(
    maxBytes = 1500,
    when = When.SECOND,
    interval = 1,
)
```

Whichever condition triggers first wins.

---

## 🔹 Retention Policies (Expiration Rules)  
RotationLogic can delete old rotated files automatically:

```python
from LogSmith import ExpirationRule, ExpirationScale

rotation = RotationLogic(
    when = When.SECOND,
    interval = 1,
    backupCount = 10,
    expiration_rule = ExpirationRule(
        scale = ExpirationScale.Days,
        interval = 7,  # delete rotated files older than 7 days
    ),
)
```

Retention is independent of rotation triggers.

---

## 🔹 Concurrency‑Safe Rotation  
LogSmith’s rotation handler is:

- **thread‑safe**  
- **process‑safe**  
- **atomic** (uses `os.replace`)  
- **cross‑platform** (fcntl on Unix, msvcrt on Windows)  

This prevents corruption when multiple threads or processes write to the same file.

**Important:**  
Multiple processes may write to the same *directory*, but not the same *base file* on Windows.

---

## 🔹 Async File Logging  
AsyncSmartLogger uses a dedicated async‑aware handler:

- rotation is scheduled in the worker thread  
- rotation never blocks the event loop  
- ordering is preserved  
- file writes are offloaded to threads  

Example:

```python
logger = AsyncSmartLogger("demo.async", level = 10)
logger.add_file(
    log_dir = str(Path(ROOT_DIR).resolve() / "logs" / "async"),    # enforces normalized path
    # absent logfile_name defaults to logger name ('demo.async')
)
```

---

## 🔹 Handler Introspection  
You can inspect all file handlers:

```python
print(logger.file_handlers)
```

Each entry includes:

- path  
- rotation settings  
- retention settings  
- sanitization mode  
- formatter type  

---

## 📘 Summary  
File logging in LogSmith provides:

- structured, readable output  
- JSON / NDJSON support  
- safe rotation (size, time, or both)  
- retention policies  
- ANSI sanitization  
- concurrency‑safe writes  
- async‑friendly behavior  
- clean handler introspection  

The next chapter dives into **Structured Formatting**, the heart of LogSmith’s output system.
