# 🚀 Quickstart  
This chapter gets you from zero to logging in under a minute — both in sync and async applications. No configuration files, no global initialization, no magic. Just create a logger, attach a handler, and start logging.

---

## 🔹Your First Logger (Sync)

SmartLogger is the synchronous logger for traditional Python applications, scripts, CLIs, and multi‑threaded workloads.

```python
from LogSmith import SmartLogger

levels = SmartLogger.levels()
logger = SmartLogger("demo", level=levels["INFO"])
logger.add_console()

logger.info("Hello from LogSmith!")
```

You now have:

- a named logger  
- a console handler  
- structured, colorized output  
- level‑aware formatting  

Nothing else is required.

---

## 🔹Your First Logger (Async)

AsyncSmartLogger is designed for asyncio applications, servers, bots, and pipelines.

```python
from LogSmith import AsyncSmartLogger, a_stdout
import asyncio

async def main():
    levels = AsyncSmartLogger.levels()
    logger = AsyncSmartLogger("demo.async", level=levels["INFO"])
    logger.add_console()

    await logger.a_info("Hello from AsyncSmartLogger!")
    await logger.flush()

asyncio.run(main())
```

AsyncSmartLogger guarantees:

- ordered log delivery  
- non‑blocking behavior  
- async rotation scheduling  
- clean shutdown via `flush()`  

---

## 🔹Adding a File Handler

File handlers are explicit. You choose where logs go and how they rotate.

```python
from LogSmith import RotationLogic, When

logger.add_file(
    log_dir="logs",
    logfile_name="app.log",
    rotation_logic=RotationLogic(
        maxBytes=50_000,
        when=When.SECOND,
        interval=1800,
        backupCount=5,
    ),
)
```

This creates:

- `logs/app.log`  
- automatic rotation (size OR time)  
- up to 5 rotated files  

---

## 🔹Structured Fields (Named Arguments)

LogSmith treats named arguments as structured fields:

```python
logger.info("User login", username="Gilad", action="login")
```

Console output includes:

```
… • INFO • User login {username='Gilad', action='login'}
```

JSON/NDJSON output includes:

```json
{
  "message": "User login",
  "fields": {
    "username": "Gilad",
    "action": "login"
  }
}
```

---

## 🔹JSON & NDJSON Logging

Switch output modes per handler:

```python
from LogSmith import OutputMode, LogRecordDetails

logger.add_console(output_mode=OutputMode.JSON)
logger.add_file(
    log_dir="logs",
    logfile_name="events.ndjson",
    output_mode=OutputMode.NDJSON,
    log_record_details=LogRecordDetails(),
)
```

- Console → pretty JSON  
- File → compact NDJSON (one JSON object per line)  

Perfect for ingestion pipelines.

---

## 🔹Raw Output (ANSI‑Preserving)

Raw output bypasses formatting and writes directly to the handler:

```python
from LogSmith import CPrint

logger.raw(CPrint.colorize("RAW colored text", fg=CPrint.FG.BRIGHT_RED))
```

Use raw output for:

- banners  
- headers  
- gradient art  
- debugging dumps  

---

## 🔹Dynamic Log Levels

Add new levels at runtime:

```python
from LogSmith import LevelStyle, CPrint

SmartLogger.register_level(
    name="NOTICE",
    value=25,
    style=LevelStyle(fg=CPrint.FG.BRIGHT_MAGENTA)
)

logger.notice("This is a NOTICE message")
```

Dynamic levels automatically become logger methods.

---

## 🔹Themes

Apply a built‑in theme:

```python
from LogSmith import DARK_THEME

SmartLogger.apply_color_theme(DARK_THEME)
logger.info("Dark theme activated!")
```

Themes affect only console output.

---

## 🔹Sync / Async Printing (stdout / a_stdout)

SmartLogger and AsyncSmartLogger includes a synchronized print() wrappers:

```python
stdout("This prints in sync with async logs")
await a_stdout("This prints in sync with async logs")
```

This prevents interleaving between print() and console logs.

---

# 🧩Summary

You now know how to:

- create sync and async loggers  
- attach console and file handlers  
- use structured fields  
- log JSON/NDJSON  
- output raw ANSI text  
- register dynamic levels  
- apply themes  
