# LogSmith  
*A modern, expressive logging framework for Python — with structure, color, gradients, async support, and rock‑solid rotation.*

LogSmith takes Python’s built‑in `logging` module and gives it the features developers actually want:

- Structured, readable log entries  
- Color and gradient console output  
- JSON and NDJSON modes  
- Async logging with ordering guarantees  
- Size‑based and time‑based rotation  
- Retention policies  
- Thread‑safe and process‑safe file handlers  
- Global auditing mode  
- Dynamic log levels  
- Themes  
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
- Like structlog → structured fields, JSON/NDJSON, predictable formatting  
- Unlike all of them →  
  - async logging engine  
  - concurrency‑safe rotation  
  - global auditing  
  - gradient engine  
  - dynamic levels  
  - raw ANSI output  
  - unified formatting model  

If you want logs that are both beautiful and machine‑friendly, LogSmith is built for you.

---

## Features at a Glance

- Structured formatting  
- Color & gradient output  
- Async logging  
- Rotation & retention  
- JSON & NDJSON  
- Themes  
- Dynamic log levels  
- Auditing mode  
- Raw ANSI output  
- Predictable behavior  

---

## Installation

LogSmith requires Python 3.10+ and has no external dependencies.

### Install from wheel

pip install logsmith‑X.Y.Z‑py3‑none‑any.whl

### Install in development mode

pip install -e .

---

## Quick Example

from LogSmith import SmartLogger, LogRecordDetails

logger = SmartLogger("demo", level=SmartLogger.levels()["INFO"])
logger.add_console()

logger.info("Hello from LogSmith!", user="Gilad", action="login")

---

## Async Example

from LogSmith import AsyncSmartLogger, a_stdout
import asyncio

async def main():
    logger = AsyncSmartLogger("async_demo", level=10)
    logger.add_console()

    await logger.a_info("Async logging works!")
    await logger.flush()

asyncio.run(main())

---

## JSON & NDJSON Example

from LogSmith import SmartLogger, OutputMode, LogRecordDetails

logger = SmartLogger("json_demo", level=10)

logger.add_console(output_mode=OutputMode.JSON)
logger.add_file(
    log_dir="logs",
    logfile_name="events.ndjson",
    output_mode=OutputMode.NDJSON,
)

---

## Rotation Example

from LogSmith import RotationLogic, When

rotation = RotationLogic(
    maxBytes=50_000,
    when=When.SECOND,
    interval=1,
    backupCount=5,
)

logger.add_file(
    log_dir="logs",
    logfile_name="rotating.log",
    rotation_logic=rotation,
)

---

## Themes Example

from LogSmith import SmartLogger, DARK_THEME

logger = SmartLogger("themed", level=10)
logger.add_console()

SmartLogger.apply_color_theme(DARK_THEME)
logger.info("Dark theme activated!")

---

## Documentation

Full documentation lives in the docs/ directory and covers:

- Console logging  
- File logging  
- Rotation & retention  
- Async logging  
- JSON/NDJSON  
- Structured formatting  
- Themes  
- Gradients  
- Auditing  
- Dynamic levels  
- Best practices  
- API reference  
- Examples gallery  

---

## Building the Wheel

Install build tools:

python tools/install_build_tools.py

Build:

python tools/build_wheel.py

Install:

pip install dist/logsmith-X.Y.Z-py3-none-any.whl

---

## Class & Package Diagrams

1. Install pylint  
2. Install Graphviz  
3. Run:

python -m pylint.pyreverse.main -o png -p LogSmith .

Outputs:

- classes_LogSmith.png  
- packages_LogSmith.png  

---

## License

MIT License — see LICENSE for details.
