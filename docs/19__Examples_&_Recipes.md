# 🔬 🧪 🧰 🪄✨🔮 Examples & Recipes  
This chapter provides ready‑to‑use patterns for common real‑world scenarios. Each recipe is self‑contained and demonstrates how to combine LogSmith features into practical logging setups for applications of all sizes.

---

## Basic Logging Setup  
A minimal, clean configuration for small scripts or CLI tools.

```python
from LogSmith import SmartLogger

levels = SmartLogger.levels()
logger = SmartLogger("demo", levels["DEBUG"])
logger.add_console()

logger.info("Hello world")
logger.debug("Debug message")
```

---

## File Logging with Rotation  
A rotating file handler for long‑running applications.

```python
from LogSmith import SmartLogger, RotationLogic

levels = SmartLogger.levels()
logger = SmartLogger("service", levels["INFO"])

logger.add_file(
    log_dir="logs",
    logfile_name="service.log",
    rotation_logic=RotationLogic(
        maxBytes=100_000,
        backupCount=5,
    ),
)
```

---

## JSON Logging for Ingestion  
NDJSON is ideal for ELK, Loki, BigQuery, and pipelines.

```python
from LogSmith import SmartLogger, OutputMode

levels = SmartLogger.levels()
logger = SmartLogger("service", levels["INFO"])

logger.add_file(
    log_dir="logs",
    logfile_name="events.ndjson",
    output_mode=OutputMode.NDJSON,
)
```

---

## Structured Fields  
Attach metadata to log entries using named arguments.

```python
logger.info("User login", username="Gilad", action="login")
```

NDJSON output:

```
{"timestamp":"...","level":"INFO","message":"User login","named_args":{"username":"Gilad","action":"login"}}
```

---

## Custom Formatting  
A fully customized structured format.

```python
from LogSmith import LogRecordDetails, OptionalRecordFields

details = LogRecordDetails(
    datefmt = "%Y-%m-%d %H:%M:%S",
    separator = "•",
    optional_record_fields = OptionalRecordFields(
        logger_name = True,
        lineno = True,
    ),
    message_parts_order  =[
        "level",
        "logger_name",
        "lineno",
    ],
)

logger.add_console(log_record_details = details)
```

---

## Themes  
Apply a built‑in theme.

```python
from LogSmith import SmartLogger, DARK_THEME

SmartLogger.apply_color_theme(DARK_THEME)
```

---

## Custom Theme  
Define your own color scheme.

```python
from LogSmith import LevelStyle, CPrint, SmartLogger

MY_THEME = {
    20: LevelStyle(fg = CPrint.FG.BRIGHT_GREEN),  # INFO
    40: LevelStyle(                             # ERROR
        fg = CPrint.FG.BRIGHT_RED,
        intensity = CPrint.Intensity.BOLD,
    ),
}

SmartLogger.apply_color_theme(MY_THEME)
```

---

## Dynamic Log Levels  
Add a new level and use it immediately.

```python
from LogSmith import SmartLogger

SmartLogger.register_level("NOTICE", 25)

logger.notice("This is a NOTICE message")
```

To style it:

```python
from LogSmith import LevelStyle, CPrint

MY_THEME = {
    25: LevelStyle(
        fg = CPrint.FG.BRIGHT_MAGENTA,
        intensity = CPrint.Intensity.BOLD,
    )
}

SmartLogger.apply_color_theme(MY_THEME)
```

---

## Async Logging  
Non‑blocking logging for asyncio applications.

```python
from LogSmith import AsyncSmartLogger

logger = AsyncSmartLogger("async.demo", level = 20)
logger.add_console()

await logger.a_info("Async message")
await logger.flush()
```

---

## Async File Logging with Rotation  
Async rotation runs in a worker thread.

```python
from LogSmith import AsyncSmartLogger, RotationLogic
from pathlib import Path

logger = AsyncSmartLogger("async.service", level = 20)

logger.add_file(
    log_dir = str(Path("logs").resolve()),
    logfile_name = "async.log",
    rotation_logic = RotationLogic(maxBytes = 50_000),
)
```

---

## Printing with Sync & Async Logging  
Prevent interleaving between print() and log messages in console.

```python
logger.stdout("This prints in sync with SmartLogger logs")
await logger.a_stdout("This prints in sync with AsyncSmartLogger logs")
```

---

## Auditing Everything  
Capture all logs from all loggers into a unified audit file.

```python
from LogSmith import SmartLogger

SmartLogger.audit_everything(
    log_dir = "audit",
    logfile_name = "audit.log",
)
```

---

## Log-Level Propagation from Parent Logger  
Set parent level to apply to self + all descendants.

```python
levels = SmartLogger.levels()

root = SmartLogger("myapp", levels["DEBUG"])
root.add_console()

api = SmartLogger("myapp.api", levels["NOTSET"])
api.add_file(log_dir="logs", logfile_name = "api.log")

users = SmartLogger("myapp.api.users", levels["NOTSET"])
users.add_file(log_dir="logs", logfile_name = "users.log")
```

---

## Exception Logging  
Structured exception output.

```python
try:
    risky_operation()
except Exception:
    logger.error(
        "Operation failed",
        operation = "risky_operation",
        exc_info = True,
    )
```

---

## Raw Output for Banners  
Use raw output for headers, banners, and gradient art.

```python
from LogSmith import CPrint, GradientPalette

logger.raw(CPrint.gradient(
    "WELCOME",
    fg_codes = GradientPalette.RAINBOW
))
```

---

## Retiring / Destroying a Logger
Decommission a logger name.

```python
logger.retire()   # disables the logger but keeps the name reserved
```

A retired logger cannot be reused.

To release the name:

```python
logger.destroy()
```

Destroying a logger does not require retiring it beforehand.

---

## Full Logger Reset  
Destroy and recreate a logger cleanly.

```python
logger.destroy()
logger = SmartLogger("myapp.module")
logger.add_console()
```

---

## 📘 Summary
These recipes demonstrate:

- basic logging  
- file logging  
- rotation  
- JSON / NDJSON  
- structured fields  
- themes  
- dynamic levels  
- async logging  
- auditing  
- multi‑module organization  
- exception handling  
- raw output  
- lifecycle operations  

The next chapter covers **Appendix A: API Reference**, providing a complete reference for all public classes, methods, and configuration objects.
