# ⚠️ Exceptions & Diagnostics

SmartLogger provides clean, readable, and structured exception logging.
It supports:

- `exc_info=True` for full tracebacks
- `stack_info=True` for stack snapshots
- structured fields + exceptions
- color‑aware console formatting
- safe file output

Diagnostics always appear **after** the main log entry.

---

## 🔹 Logging Exceptions with `exc_info=True`

```python
try:
    1 / 0
except ZeroDivisionError:
    logger.error("Computation failed", exc_info=True)
```

---

## 🔹 Structured Fields + Exceptions

```python
try:
    risky_operation()
except Exception:
    logger.error("Operation failed", op="risky_operation", exc_info=True)
```

---

## 🔹 Stack Snapshots with `stack_info=True`

```python
logger.debug("Debug snapshot", stack_info=True)
```

---

## 🔹 Multi‑Line Diagnostics Formatting

- tracebacks printed after the log entry
- indentation preserved
- console keeps color
- file handlers sanitize ANSI, unless sanitization is disabled

---

## 🔹 Diagnostics in File Handlers

```python
logger.add_file("logs", "errors.log")
logger.error("Failure", exc_info=True)
```

---

# 🧩 Summary

SmartLogger’s diagnostics system provides:

- clean exception logging
- structured fields + tracebacks
- stack snapshots
- color‑aware console output
- safe file output
- predictable multi‑line formatting
