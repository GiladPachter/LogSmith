# ♻️ Rotation & Retention
Log rotation is one of the hardest parts of logging systems. It must be safe, predictable, atomic, and compatible with multi‑threaded and multi‑process workloads. LogSmith’s rotation engine is designed to handle all of this cleanly, both in synchronous and asynchronous environments.

This chapter explains rotation triggers, retention policies, timestamp anchors, concurrency guarantees, and how rotation integrates with SmartLogger and AsyncSmartLogger.

---

## 💡 Why Rotation Matters
Without rotation, log files grow indefinitely. This leads to:

- disk exhaustion  
- slow file operations  
- difficult log ingestion  
- unbounded retention  
- corrupted logs during manual rotation  

LogSmith solves these problems with:

- size‑based rotation  
- time‑based rotation  
- hybrid rotation (size OR time)  
- retention policies  
- concurrency‑safe file operations  
- async‑aware rotation scheduling  

---

## 🔹 RotationLogic: The Core Object
Rotation is configured using a `RotationLogic` object:

```python
from LogSmith import RotationLogic, When

rotation = RotationLogic(
    maxBytes    = 50_000,
    when        = When.SECOND,
    interval    = 1800,
    backupCount = 5,
)
```

Attach it to a file handler:

```python
logger.add_file(
    log_dir        = "logs",
    logfile_name   = "app.log",
    rotation_logic = rotation,
)
```

---

## 🔹 Size‑Based Rotation
Rotate when the file exceeds a maximum size:

```python
RotationLogic(maxBytes = 100_000, backupCount = 10)
```

Ideal for:

- CLI tools  
- services with unpredictable log volume  
- environments with strict disk quotas  

Rotation occurs immediately after a write pushes the file over the threshold.

---

## 🔹 Time‑Based Rotation
Rotate on a schedule:

```python
RotationLogic(
    when     = When.MINUTE,
    interval = 5,  # rotate every 5 minutes
)
```

Supported time units:

- SECOND  
- MINUTE  
- HOUR  
- EVERYDAY  
- MONDAY  
- TUESDAY  
- …  
- SUNDAY  

Daily/weekly rotation uses a timestamp anchor.

---

## 🔹 Timestamp Anchors
For daily/weekly rotation, you can specify the exact time of day:

```python
from LogSmith import RotationTimestamp

RotationLogic(
    when      = When.EVERYDAY,
    timestamp = RotationTimestamp(hour = 0, minute = 0, second = 0),
)
```

This rotates at midnight every day.

Weekly rotation example:

```python
RotationLogic(
    when      = When.MONDAY,
    timestamp = RotationTimestamp(hour = 3),
)
```

Rotates every Monday at 03:00.

---

## 🔹 Hybrid Rotation (Size OR Time)
LogSmith supports hybrid rotation:

```python
RotationLogic(
    maxBytes = 1500,
    when     = When.SECOND,
    interval = 1,
)
```

Whichever condition triggers first wins.

This is ideal for:

- high‑volume logs  
- long‑running services  
- ingestion pipelines  

---

## 🔹 Rotation File Naming
Rotated files follow this pattern:

```
app.log
app.log.1
app.log.2
app.log.3
...
```

The timestamp is precise to the second.

If `backupCount` is set, older rotated files are deleted automatically.

---

## 🔹 Retention Policies (Expiration Rules)
Retention is controlled by an `ExpirationRule`:

```python
from LogSmith import ExpirationRule, ExpirationScale

ExpirationRule(
    scale    = ExpirationScale.Days,
    interval = 7,  # delete rotated files older than 7 days
)
```

Attach it to rotation:

```python
rotation = RotationLogic(
    when = When.SECOND,
    interval    = 1,
    backupCount = 10,
    expiration_rule = ExpirationRule(
        scale    = ExpirationScale.Days,
        interval = 7,
    ),
)
```

Retention is evaluated after each rotation.

---

## 🔹 Concurrency‑Safe Rotation
Rotation must be safe even when multiple threads or processes write to the same file.

LogSmith uses:

- `fcntl` locks on Unix  
- `msvcrt` locks on Windows  
- atomic `os.replace()` for renaming  
- per‑handler locking  

This ensures:

- no partial writes  
- no corrupted rotated files  
- no race conditions  
- no interleaving during rotation  

**Important:**  
On Windows, multiple processes should not write to the same base file.  
Use per‑process log files instead.

---

## 🔹 Rotation in AsyncSmartLogger
AsyncSmartLogger handles rotation in its worker thread:

- rotation checks do not block the event loop  
- file operations run in a thread pool  
- ordering is preserved  
- rotation is atomic  

Example:

```python
logger = AsyncSmartLogger("demo.async", level = 10)

logger.add_file(
    log_dir        = "logs",
    logfile_name   = "async.log",
    rotation_logic = RotationLogic(maxBytes = 50_000),
)
```

---

## 🔹 Rotation + JSON / NDJSON
Rotation works identically for JSON and NDJSON:

```python
logger.add_file(
    log_dir        = "logs",
    logfile_name   = "events.ndjson",
    output_mode    = OutputMode.NDJSON,
    rotation_logic = RotationLogic(maxBytes = 50_000),
)
```

Rotated files remain valid NDJSON.

---

## 🔹 Rotation + Raw Output
Raw output is also rotated safely:

```python
logger.raw("RAW text")
```

ANSI is sanitized unless disabled.

---

## 🔹 Inspecting Rotation State
You can inspect rotation settings:

```python
print(logger.file_handlers)
```

Each handler reports:

- rotation logic  
- retention policy  
- next scheduled rotation time  
- current file size  

---

## 🧩 Summary
LogSmith’s rotation engine provides:

- size‑based rotation  
- time‑based rotation  
- hybrid rotation  
- timestamp anchors  
- retention policies  
- concurrency‑safe file operations  
- async‑aware rotation scheduling  
- atomic renaming  
- JSON / NDJSON compatibility
