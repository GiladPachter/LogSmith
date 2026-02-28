# Core Concepts  
LogSmith builds on Python’s logging module but reshapes it into a modern, structured, expressive system. Understanding these core ideas will help you get the most out of both SmartLogger and AsyncSmartLogger.

---

## Logging as a Structured Event  
Traditional logging treats a log entry as a formatted string. LogSmith treats it as a **structured event**:

- timestamp  
- level  
- message  
- optional metadata (file, line, thread, process, logger name)  
- structured fields (named arguments)  
- exception info  
- stack info  

This structure is preserved across:

- console output  
- file output  
- JSON  
- NDJSON  
- auditing  

You choose which fields appear and in what order.

---

## LogRecordDetails: The Formatting Blueprint  
Instead of format strings, LogSmith uses a declarative object:

```python
from LogSmith import LogRecordDetails, OptionalRecordFields

details = LogRecordDetails(
    datefmt="%Y-%m-%d %H:%M:%S.%3f",
    separator="•",
    optional_record_fields=OptionalRecordFields(
        file_name=True,
        lineno=True,
        func_name=True,
    ),
    message_parts_order=[
        "level",
        "file_name",
        "lineno",
        "func_name",
    ],
    color_all_log_record_fields=False,
)
```

This controls:

- timestamp formatting  
- which fields appear  
- the order of fields  
- how color is applied  
- how exceptions and stack traces are shown  

It’s the backbone of LogSmith’s formatting system.

---

## Output Modes  
Each handler chooses its own output mode:

- **PLAIN** — structured text, no color  
- **COLOR** — structured text with ANSI colors  
- **JSON** — pretty‑printed JSON  
- **NDJSON** — compact JSON, one object per line  

This lets you mix:

- colorized console output  
- NDJSON ingestion logs  
- JSON debugging logs  
- plain text audit logs  

All from the same logger.

---

## Handlers: Explicit and Predictable  
LogSmith does not guess where logs should go.  
You attach handlers explicitly:

```python
logger.add_console()
logger.add_file(log_dir="logs", logfile_name="app.log")
```

A logger may have:

- **0 or 1 console handler**
- **0 or many file handlers**

Handlers never propagate upward unless auditing is enabled.

---

## Rotation Logic  
Rotation is handled by a dedicated object:

```python
from LogSmith import RotationLogic, When

rotation = RotationLogic(
    maxBytes=50_000,
    when=When.SECOND,
    interval=1,
    backupCount=5,
)
```

Rotation triggers when **either** condition is met:

- file exceeds `maxBytes`  
- current time passes the next scheduled rotation moment  

Rotation is:

- thread‑safe  
- process‑safe  
- atomic  
- predictable  

AsyncSmartLogger schedules rotation in its worker thread.

---

## Retention Policies  
RotationLogic can also delete old rotated files:

```python
from LogSmith import ExpirationRule, ExpirationScale

ExpirationRule(scale=ExpirationScale.Days, interval=7)
```

This keeps log directories clean without external scripts.

---

## Structured Fields (Named Arguments)  
Named arguments become structured fields:

```python
logger.info("User login", username="Gilad", action="login")
```

Console output:

```
… • INFO • User login {username='Gilad', action='login'}
```

JSON/NDJSON output:

```json
{
  "message": "User login",
  "fields": {
    "username": "Gilad",
    "action": "login"
  }
}
```

This makes LogSmith ideal for ingestion pipelines.

---

## Color Engine & Gradients  
LogSmith includes a full ANSI engine:

- solid colors  
- intensity (bold, dim)  
- styles (underline, italic, strike)  
- foreground/background  
- 256‑color gradients  
- palette blending  

Example:

```python
from LogSmith import CPrint, GradientPalette

logger.raw(CPrint.gradient("Hello", fg_codes=GradientPalette.RAINBOW))
```

---

## Themes  
Themes map log levels to colors:

```python
from LogSmith import DARK_THEME
SmartLogger.apply_color_theme(DARK_THEME)
```

Themes affect only console output and can be reset at any time.

---

## Dynamic Log Levels  
You can register new levels at runtime:

```python
SmartLogger.register_level("NOTICE", 25)
logger.notice("Hello")
```

Dynamic levels automatically become logger methods.

---

## Hierarchy  
Logger names define hierarchy:

```
myapp
myapp.api
myapp.api.users
```

Rules:

- A logger with level NOTSET inherits from its parent  
- Handlers do **not** propagate unless auditing is enabled  
- Each logger manages its own handlers independently  

This keeps large applications organized.

---

## Auditing  
Auditing captures **all** loggers into a single file:

```python
SmartLogger.audit_everything(log_dir="audit", logfile_name="audit.log")
```

Auditing:

- enables propagation  
- uses AuditFormatter  
- supports rotation  
- can be disabled cleanly  

AsyncSmartLogger has its own async auditing system.

---

## Raw Output  
Raw output bypasses formatting:

```python
logger.raw("This is raw text")
```

Useful for:

- banners  
- headers  
- gradient art  
- debugging dumps  

File handlers sanitize ANSI unless explicitly told not to.

---

## Async Logging Model  
AsyncSmartLogger uses:

- an asyncio queue  
- a worker task  
- ordered delivery  
- async rotation scheduling  
- synchronized printing via `a_stdout()`  

This keeps your event loop clean and responsive.

---

## Logger Lifecycle  
Loggers can be:

- **retired** — handlers closed, logger disabled  
- **destroyed** — removed from logging system entirely  

This allows clean recreation of loggers with the same name.

---

## Summary  
These concepts form the foundation of LogSmith:

- structured events  
- declarative formatting  
- explicit handlers  
- safe rotation  
- async support  
- themes and gradients  
- dynamic levels  
- auditing  
- predictable hierarchy  
- raw output  

The next chapter explores console logging in depth — color, gradients, formatting, and customization.
