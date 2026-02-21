# 🔄 Rotation Logic

LogSmith provides a powerful, flexible, and concurrency‑safe rotation system that supports:

- **Size‑based rotation**
- **Time‑based rotation** (second, minute, hour, daily, weekly)
- **Hybrid rotation** (size OR time)
- **Retention policies** (delete old rotated files)
- **PID and timestamp suffixing**
- **Cross‑process‑safe rollover**
- **Atomic renames**

All rotation behavior is configured through `RotationLogic`.

---

## 🔹 Creating Rotation Logic

```python
from LogSmith import RotationLogic, When

rotation = RotationLogic(
    maxBytes=50_000,
    when=When.SECOND,
    interval=1,
    backupCount=10,
)
```

Attach it to a file handler:

```python
logger.add_file(
    log_dir = "logs",
    logfile_name = "app.log",
    rotation_logic = rotation,
)
```

---

# 🧱 Rotation Modes

## 1. Size‑Based Rotation

Triggered when the active log file exceeds `maxBytes`.

```python
RotationLogic(maxBytes = 100_000, backupCount = 5)
```

Creates:

```
app.log
app.log.1
app.log.2
...
```

---

## 2. Time‑Based Rotation

### ✔ Rotate every N seconds

```python
RotationLogic(when = When.SECOND, interval=5)
```

### ✔ Rotate every N minutes

```python
RotationLogic(when = When.MINUTE, interval = 10)
```

### ✔ Rotate every N hours

```python
RotationLogic(when = When.HOUR, interval = 1)
```

---

## 3. Daily Rotation (at a specific time)

```python
from LogSmith import RotationTimestamp

RotationLogic(
    when=When.EVERYDAY,
    timestamp=RotationTimestamp(hour=0, minute=0, second=0),  # midnight
)
```

---

## 4. Weekly Rotation (at a specific time)

```python
RotationLogic(
    when = When.MONDAY,
    timestamp = RotationTimestamp(hour = 3, minute = 0),
)
```

Supported weekdays:

```
MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY
```

---

## 5. Hybrid Rotation (size OR time)

SmartLogger rotates when **either** condition is met:

```python
RotationLogic(
    maxBytes = 50_000,
    when = When.HOUR,
    interval = 1,
)
```

This is ideal for high‑volume logs.

---

# 🧹 Retention Policies (Expiration Rules)

SmartLogger can automatically delete old rotated files.

```python
from LogSmith import ExpirationRule, ExpirationScale

RotationLogic(
    when=When.SECOND,
    interval=1,
    backupCount=10,
    expiration_rule=ExpirationRule(
        scale=ExpirationScale.Seconds,
        interval=5,  # delete rotated files older than 5 seconds
    ),
)
```
---

## ✔ PID Suffix

```python
RotationLogic(append_filename_pid = True)
```

Produces:

```
app.12345.log
```

Useful for multi‑process applications.

# 🧩 Filename Suffixing

## ✔ Timestamp Suffix

```python
RotationLogic(append_filename_timestamp = True)
```

Produces:

```
app_20240210_213045.log
```

---

# 🔐 Concurrency‑Safe Rotation

LogSmith’s handler uses:

- `fcntl` locks on Unix
- `msvcrt` locks on Windows
- atomic renames (`os.replace`)
- lock files (`.lock`)

This prevents corruption when multiple processes write to the same file.

---

# 🧩 Summary

LogSmith’s rotation system provides:

- flexible size / time rotation
- daily / weekly scheduling
- hybrid rotation
- retention policies
- PID / timestamp suffixing
- concurrency‑safe rollover
- atomic file operations

This makes it suitable for production‑grade logging in demanding environments.
