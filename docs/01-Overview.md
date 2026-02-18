# 📘 SmartLogger
*A high‑performance, structured, color‑aware logging framework for Python*

SmartLogger is a modern logging framework that builds on Python’s standard `logging` module and elevates it with:

- **Structured formatting** (timestamp, level, file, line, thread, process, extras)
- **Color and gradient output** (ANSI, 256‑color palettes, foreground/background gradients)
- **Size‑based, time‑based, and hybrid rotation**
- **Retention policies** (delete old rotated files automatically)
- **Concurrency‑safe file handlers** (thread‑safe and cross‑process‑safe)
- **Global auditing mode** (capture *all* loggers into a single audit file)
- **Dynamic log levels** (register new levels at runtime)
- **Themes** (light, dark, neon, pastel)
- **Raw output** (write colored text directly to console or file)
- **Hierarchical logger behavior** (parent/child inheritance)
- **Drop‑in compatibility** with Python’s logging API

SmartLogger is designed for:

- CLI tools
- Services and daemons
- Multi‑threaded applications
- Multi‑process applications (with per‑process files)
- Debugging utilities
- Any application that benefits from readable, structured, expressive logs

SmartLogger aims to be a **drop‑in replacement** for Python’s logging module when you want:

- cleaner APIs
- richer formatting
- safer rotation
- global auditing
- colorized and gradient‑enhanced console output
- predictable behavior across an entire application
