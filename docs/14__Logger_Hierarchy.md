# 🌳 Logger Hierarchy

LogSmith uses a predictable, explicit hierarchy model inspired by Python’s built‑in logging system but redesigned to avoid the pitfalls of implicit propagation, handler duplication, and confusing inheritance. This chapter explains how logger names define hierarchy, how levels are inherited, how handlers behave, and how to structure large applications cleanly.

---

## 🧬 How Logger Hierarchy Works

Logger names define a tree structure:

```
myapp
myapp.api
myapp.api.users
myapp.api.orders
myapp.worker
```

Each dot (`.`) creates a parent–child relationship:

- `myapp` is the parent of `myapp.api`
- `myapp.api` is the parent of `myapp.api.users`
- and so on

Hierarchy affects:

- level inheritance  
- propagation (only when auditing is enabled)  
- organization of large applications  

Handlers **never propagate** unless auditing is active.

LogSmith improves on Python’s logging by enforcing **explicit hierarchy creation**:

- A logger cannot be created if its parent does not already exist.  
- A logger cannot be created if its parent exists but is of a different type (SmartLogger vs AsyncSmartLogger).  

This prevents accidental mixed hierarchies and undefined behavior.

---

## 🏗️ Creating Loggers in a Hierarchy

You must create loggers **from the top down**:

```python
root  = SmartLogger("myapp", level = 20)
api   = SmartLogger("myapp.api")
users = SmartLogger("myapp.api.users")
```

If a parent logger does not exist, LogSmith raises an error:

```
RuntimeError: Cannot create logger 'myapp.api.users' because ancestor 'myapp.api' does not exist.
```

This ensures hierarchy is always intentional.

---

## 🔢 Level Inheritance

Level inheritance follows these rules:

- If a logger’s level is NOTSET → inherit from parent  
- If a logger has an explicit level → use that level  
- If no parent has an explicit level → default to INFO  

Example:

```python
root  = SmartLogger("myapp", level = 30)  # WARNING
api   = SmartLogger("myapp.api")          # inherits WARNING
users = SmartLogger("myapp.api.users", level = 10)  # DEBUG
```

`users` logs DEBUG and above, while `api` logs WARNING and above.

---

## 🧰 Handler Behavior

LogSmith’s handler model is intentionally simple:

- **Handlers do NOT propagate upward**  
- **Each logger manages its own handlers**  
- **Console handlers: max 1 per logger**  
- **File handlers: any number per logger**  
- **Duplicate file handlers are prevented process‑wide**  

This avoids the classic “logger soup” problem where multiple handlers accidentally duplicate output.

Example:

```python
root.add_console()
api.add_file(log_dir = "logs", logfile_name = "api.log")
users.add_file(log_dir = "logs", logfile_name = "users.log")
```

Each logger writes only to its own handlers.

---

## 🔄 Propagation and Auditing

Propagation is disabled by default.<br/>
It is enabled only when auditing is turned on:

```python
SmartLogger.audit_everything(
    log_dir = "audit",
    logfile_name = "audit.log",
)
```

When auditing is active:

- all loggers propagate upward  
- the audit handler receives all events  
- individual handlers still work normally  

This provides a global audit trail without interfering with normal logging behavior.

---

## 🔍 Logger Discovery

LogSmith does **not** auto‑create missing loggers.

To retrieve an existing logger, use Python’s logging manager:

```python
import logging
logger = logging.getLogger("myapp.api.users")
```

If the logger was created via SmartLogger, this returns the same underlying Python logger.

To create a new SmartLogger, you must explicitly instantiate it:

```python
users = SmartLogger("myapp.api.users")
```

If the hierarchy is invalid, LogSmith raises an error.

---

## 🛑 Retiring or Destroying Loggers

Loggers can be retired or destroyed depending on your needs.

### Retiring a logger

```python
logger.retire()
```

This:

- closes all handlers  
- removes them from the logger  
- marks the logger as unusable  

### Destroying a logger

```python
logger.destroy()
```

This:

- retires the logger  
- removes it from the logging system  
- detaches it from its parent  
- re‑parents children to root  
- allows clean recreation:

```python
logger = SmartLogger("myapp.api.users")
```

---

## Organizing Large Applications

A common pattern:

```
myapp
myapp.api
myapp.api.users
myapp.api.orders
myapp.worker
myapp.db
```

Recommended structure:

- attach a console handler only to the root logger  
- attach file handlers to specific modules  
- use dynamic levels for domain‑specific events  
- enable auditing in production  

Example:

```python
root = SmartLogger("myapp", level=20)
root.add_console()

api = SmartLogger("myapp.api")
api.add_file(log_dir = "logs", logfile_name = "api.log")

users = SmartLogger("myapp.api.users")
users.add_file(log_dir = "logs", logfile_name = "users.log")
```

---

## 🌀 Hierarchy in AsyncSmartLogger

AsyncSmartLogger uses the same hierarchy rules:

```python
root  = AsyncSmartLogger("service")
api   = AsyncSmartLogger("service.api")
users = AsyncSmartLogger("service.api.users")
```

Additional async‑specific rules:

- parents must be AsyncSmartLogger instances  
- SmartLogger and AsyncSmartLogger cannot share hierarchy branches  
- async auditing uses a dedicated async audit logger  

Async logging methods (`a_info`, `a_error`, etc.) work identically across the hierarchy.

---

## 🧠 Best Practices

- Use dot‑separated names to mirror your module structure.  
- Create loggers top‑down to avoid hierarchy errors.  
- Set levels at higher nodes and inherit downward.  
- Attach console handlers only to the root logger.  
- Attach file handlers to specific modules.  
- Use auditing for global capture.  
- Avoid attaching many handlers to many loggers — keep it clean.  

---

## 📘 Summary

Logger hierarchy in LogSmith provides:

- predictable parent–child relationships  
- strict ancestor validation  
- clean level inheritance  
- non‑propagating handlers  
- optional global auditing  
- easy organization for large applications  
- identical behavior for sync and async loggers  
- safe retirement and recreation of loggers  

The next chapter covers **Lifecycle Management** — how loggers are created, retired, destroyed, and safely shut down.
