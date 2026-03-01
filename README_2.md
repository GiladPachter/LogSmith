# 📘 LogSmith  
*A modern, expressive logging framework for Python — with structure, color, gradients, async support, and rock‑solid rotation.*

LogSmith takes Python’s built‑in `logging` module and gives it the features developers actually want:

- Structured, user-friendly log message formatting
- Colored messages, color themes and gradient console output  
- Size‑based and time‑based rotation - intermixed when useful
- Thread‑safe and process‑safe file handlers  
- Retention policies  
- Global auditing mode  
- Dynamic log levels  
- JSON and NDJSON modes  
- Async logging with ordering guarantees  
- Raw ANSI output  
- Predictable, explicit behavior  

It’s designed for CLI tools, services, daemons, debugging utilities, and any application that benefits from clean, expressive logs.

---

## Why LogSmith?

Python’s standard logging module is powerful but low‑level.  
Rich is beautiful but not built for structured logging or rotation.  
structlog is structured but not color‑first or rotation‑aware.

LogSmith combines the strengths of all three:

- Like Python logging → familiar API, handlers, levels, propagation rules  
- Like Rich → expressive color output, gradients, themes  
- Like structlog → structured fields, JSON / NDJSON, predictable formatting  
- Unlike all of them →  
  - async logging engine  
  - concurrency‑safe rotation  
  - raw ANSI output  
  - gradient engine  
  - dynamic log levels  
  - unified formatting model
  - perfect logging and non-logging console output synchronization

If you want logs that are both beautiful and machine‑friendly, LogSmith is built for you.

---

## Installation

LogSmith requires Python 3.10+ and has no external dependencies.

### Install from wheel

pip install logsmith‑X.Y.Z‑py3‑none‑any.whl

### Install in development mode

pip install -e .

---

# 🚀 Quick Example

```python
from LogSmith import SmartLogger

levels = SmartLogger.levels()
logger = SmartLogger("async-demo", levels["DEBUG"])
logger.add_console()
logger.info("Hello from a_sync")    # >>> 2026-02-28 15:14:31.705 • INFO     • Hello from LogSmith
```

```
>>>  2026-02-28 15:14:31.705 • INFO     • Hello from LogSmith
```

---

## Async Example
```python
import asyncio
from LogSmith import AsyncSmartLogger

async def main():

    levels = AsyncSmartLogger.levels()
    logger = AsyncSmartLogger("async-demo", levels["DEBUG"])
    logger.add_console()

    await logger.a_info("Hello from a_sync")

asyncio.run(main())
```

```
>>>  2026-02-28 15:14:31.705 • INFO     • Hello from a_sync
```

---

## JSON & NDJSON Example

```python
from pathlib import Path
from LogSmith import SmartLogger, OutputMode, LogRecordDetails, OptionalRecordFields
from project_definitions import ROOT_DIR

logger = SmartLogger("json_demo", level=10)

logger.add_console(output_mode=OutputMode.JSON)
logger.add_file(
    log_dir = str(Path(ROOT_DIR).resolve() / "logs" / "NDJSON"),    # enforces normalized path
    logfile_name="events.ndjson",
    output_mode=OutputMode.NDJSON,
)

logger.info("Hello NDJSON")
```
Console output (JSON):
```
>>> {
>>>     "timestamp": "2026-02-28T16:16:03.612583+00:00",
>>>     "level": "INFO",
>>>     "message": "Hello NDJSON",
>>>     "fields": {}
>>> }
```
file output (NDJSON):
```
>>> {"timestamp": "2026-02-28T16:16:03.612583+00:00", "level": "INFO", "message": "Hello NDJSON", "fields": {}}
```

---

## Rotation Example

```python
from LogSmith import SmartLogger
from LogSmith import RotationLogic, When

levels = SmartLogger.levels()
logger = SmartLogger("async-demo", levels["DEBUG"])

logger.add_file(
    log_dir="logs",
    logfile_name = "rotating.log",
    rotation_logic = RotationLogic(
                     maxBytes=50_000,
                     when=When.SECOND,
                     interval=1800,
                     backupCount=5,
                     ),
)
```

---

## Themes Example
```python
from LogSmith import SmartLogger, DARK_THEME

logger = SmartLogger("themed", level=10)
logger.add_console()

SmartLogger.apply_color_theme(DARK_THEME)
logger.info("Dark theme applied!")
```

---

# 📚 Documentation

Full documentation lives in the docs/ directory and covers:

- Console logging  
- File logging  
- Rotation & retention  
- Async logging  
- JSON / NDJSON  
- Structured formatting  
- Themes  
- Gradients  
- Auditing  
- Dynamic levels  
- Best practices  
- API reference  
- Examples gallery  

---

# 🔧 Building the Wheel

Install build tools:

python tools/install_build_tools.py

Build:

python tools/build_wheel.py

Install:

pip install dist/logsmith-X.Y.Z-py3-none-any.whl

---

# 🔧 Class & Package Diagrams

1. Install pylint  
2. Install Graphviz  
3. Run:

```console/terminal
python -m pylint.pyreverse.main -o png -p LogSmith .
```

Outputs:

- classes_LogSmith.png  
- packages_LogSmith.png  

---

## License

MIT License — see LICENSE for details.
