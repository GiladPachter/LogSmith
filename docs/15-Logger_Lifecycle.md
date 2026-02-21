# 🔄 Logger Lifecycle

LogSmith provides explicit lifecycle management for loggers.
This ensures that:
- handlers are not leaked
- stale loggers do not accumulate
- loggers can be safely recreated
- resources are properly released

---

# 🔹 Creating a Logger

```python
logger = SmartLogger.get("myapp.module")
```

`SmartLogger.get()` ensures:
- the logger is a **SmartLogger** instance
- stale loggers with the same name are cleaned up
- the logger is registered in the SmartLogger registry
- the logger starts with no handlers. Each desired handler must be added explicitly.

---

# 🔹 Retiring a Logger

```python
logger.retire()
```

Retiring a logger:
- closes all handlers
- flushes buffers
- marks the logger as inactive
- prevents further logging
- keeps the name reserved

---

# 🔹 Destroying a Logger

```python
logger.destroy()
```

Destroying a logger:
- removes it from the SmartLogger registry
- closes all handlers
- allows a new logger with the same name to be created

---

# 🔹 Recreating a Logger After Destruction

```python
logger.destroy()
logger = SmartLogger.get("myapp.module")
```

---

# 🔹 Checking Logger State
```python
logger.retired
logger.handlers
logger.console_handler
logger.file_handlers
```
---

# 🔹 Best Practices
- Use `retire()` to disable a logger and preventing reuse of logger name
- Use `destroy()` to remove a logger completely and allow reuse of logger name

---

# 🧩 Summary
LogSmith’s lifecycle management provides:
- explicit control over logger creation
- safe retirement and destruction
- clean recreation without stale handlers
- global shutdown support
- predictable behavior in dynamic environments
