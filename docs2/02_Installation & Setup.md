# Installation & Setup  
LogSmith is pure Python, dependency‑free, and works on all major platforms. This chapter walks you through installing it, verifying your environment, and understanding the minimal setup needed before creating your first logger.

---

## Requirements

LogSmith is intentionally lightweight:

- **Python 3.10+**
- **No external dependencies**
- **ANSI‑capable terminal** (for color output)
- **Standard OS file system** (for rotation and retention)
- **fcntl** (Unix) or **msvcrt** (Windows) for concurrency‑safe rotation

If your terminal supports ANSI colors, LogSmith will automatically detect it. If not, it gracefully falls back to plain output.

---

## Installing LogSmith

### Install from wheel (recommended)

If you have a `.whl` file:

```
pip install logsmith‑X.Y.Z‑py3‑none‑any.whl
```

Replace `X.Y.Z` with the version you built or downloaded.

### Install in development mode

If you’re working directly with the source tree:

```
pip install -e .
```

This lets you edit the codebase and immediately test changes without reinstalling.

---

## Building the Wheel (optional)

LogSmith includes helper scripts for building distributable wheels.

### 1. Install build tools

```
python tools/install_build_tools.py
```

### 2. Build the wheel

```
python tools/build_wheel.py
```

The resulting file appears under `dist/`, for example:

```
dist/logsmith-1.8.0-py3-none-any.whl
```

---

## Verifying Your Installation

Run the following:

```python
import LogSmith
print(LogSmith.__version__)
```

If this prints a version string, your installation is good to go.

---

## Project Layout (for contributors)

A typical LogSmith checkout looks like this:

```
LogSmith/
├─ docs/              # documentation (this book)
├─ examples/          # runnable demos
├─ LogSmith/          # the actual library
├─ tools/             # wheel-building helpers
├─ pyproject.toml     # packaging metadata
└─ README.md
```

You can run any example directly:

```
python examples/01_basic_logging.py
```

---

## Initialization Requirements

### SmartLogger (sync)

SmartLogger does **not** require global initialization anymore.  
You can create loggers immediately:

```python
from LogSmith import SmartLogger
logger = SmartLogger("demo", level=10)
logger.add_console()
```

### AsyncSmartLogger (async)

AsyncSmartLogger also requires **no global init**.  
It integrates directly with `asyncio`:

```python
from LogSmith import AsyncSmartLogger
logger = AsyncSmartLogger("demo.async", level=10)
logger.add_console()
```

Both logger types are ready to use as soon as you instantiate them.

---

## Platform Notes

### Linux & macOS
- Uses `fcntl` for concurrency‑safe rotation  
- Fully supports ANSI colors  
- Ideal environment for multi‑process logging

### Windows
- Uses `msvcrt` for rotation locking  
- ANSI colors supported in modern terminals (Windows Terminal, VSCode, PyCharm)

### WSL
- Fully supported  
- Behaves like Linux

---

## Summary

- Install via wheel or editable mode  
- No global initialization required  
- Works on all major platforms  
- No dependencies  
- Ready for both sync and async applications  

The next chapter walks you through a complete Quickstart so you can create your first logger in under a minute.
