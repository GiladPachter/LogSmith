# 🚀 Quick Start

LogSmith requires a one‑time global initialization at application startup.</br>
After that, you can create loggers, attach handlers, and start logging immediately.

---

## 1. Initialize LogSmith

```python
from LogSmith import SmartLogger

levels = SmartLogger.levels()
SmartLogger.initialize_smartlogger(level=levels["INFO"])
```
This is an essential preliminary step at the start of any process that makes use of LogSmith.</br>
LogSmith replaces Python’s root logger with a SmartLogger root and ensures consistent behavior across all loggers.

---

## 2. Create a logger
```python
logger = SmartLogger.get("demo", level = levels["INFO"])
```
Each logger has its own level and its own handlers.

---

## 3. Add a console handler
```python
logger.add_console(level = levels["INFO"])
```
Console output is automatically colorized using LogSmith’s structured formatter.

---

## 4. Log messages
```python
logger.info("Hello from LogSmith!")
logger.warning("Something might be wrong")
logger.error("Something *is* wrong")
```

---

## 5. Optional: Add a file handler

```python
from LogSmith import RotationLogic

logger.add_file(
    log_dir="logs",
    logfile_name="demo.log",
    rotation_logic=RotationLogic(maxBytes=50_000, backupCount=5),
)
```

This enables size‑based rotation with retention.

---

## ✔ Result

You now have:
- a fully initialized logging system
- structured, colorized console output
- optional rotating file output
- a logger ready for production use
