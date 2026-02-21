## 📦 Installation

To begin using LogSmith, install the package and initialize the logging system at application startup.</br>
LogSmith requires **Python 3.10+** and has **<u>no external dependencies</u>**.

---

## 🔧 Install from wheel

---
bash:
```
pip install logsmith‑0.1.0‑py3‑none‑any.whl
```

---

## 🔧 Install in development mode

If you are working with the source tree:

```bash
pip install -e .
```

This allows live editing of the LogSmith codebase without reinstalling.

---

## ⚙️ Minimum Requirements

- Python **3.10 or newer**
- A terminal that supports ANSI colors
- For concurrency‑safe rotation:
  - Linux/macOS: uses `fcntl`
  - Windows: uses `msvcrt`

LogSmith automatically detects platform capabilities and falls back gracefully when needed.

---

## 🧪 Verify installation

```python
import LogSmith

print(LogSmith.__version__)
```

---

## 📁 Project Layout (for development)

```
LogSmith/
├─ docs/          # documentation
├─ examples/      # usage demonstration
├─ LogSmith/      # product logic
├─ tools/         # conversion to '.whl' & '.tar.gz'
└─ pyproject.toml
```

You can run any demo directly:

```bash
python examples/basic_console.py
```
