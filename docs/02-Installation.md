## 📦 Installation

To begin using SmartLogger, install the package and initialize the logging system at application startup.</br>
SmartLogger requires **Python 3.10+** and has **<u>no external dependencies</u>**.

---

## 🔧 Install from wheel

---
bash:
```
pip install smartlogger‑0.1.0‑py3‑none‑any.whl
```

---

## 🔧 Install in development mode

If you are working with the source tree:

```bash
pip install -e .
```

This allows live editing of the SmartLogger codebase without reinstalling.

---

## ⚙️ Minimum Requirements

- Python **3.10 or newer**
- A terminal that supports ANSI colors
- For concurrency‑safe rotation:
  - Linux/macOS: uses `fcntl`
  - Windows: uses `msvcrt`

SmartLogger automatically detects platform capabilities and falls back gracefully when needed.

---

## 🧪 Verify installation

```python
import LogSmith

print(LogSmith.__version__)
```

---

## 📁 Project Layout (for development)

```
LoggerEx/
├─ docs/          # documentation
├─ examples/      # usage demonstration
├─ smartlogger/   # product logic
├─ tools/         # conversion to '.whl' & '.tar.gz'
└─ pyproject.toml
```

You can run any demo directly:

```bash
python examples/basic_console.py
```
