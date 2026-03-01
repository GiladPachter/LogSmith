# 🌳 Logger Hierarchy  
LogSmith uses a predictable, explicit hierarchy model inspired by Python’s built‑in logging system but redesigned to avoid the pitfalls of implicit propagation, handler duplication, and confusing inheritance. This chapter explains how logger names define hierarchy, how levels are inherited, how handlers behave, and how to structure large applications cleanly.

---

## How Logger Hierarchy Works  
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
- propagation (when auditing is enabled)  
- organization of large applications  

Handlers do **not** propagate by default — this is a major improvement over Python’s logging module.

---

## Creating Loggers in a Hierarchy  
You can create loggers anywhere in the hierarchy:

```python
root = SmartLogger("myapp", level=20)
api = SmartLogger("myapp.api")
users = SmartLogger("myapp.api.users")
```

If a logger’s level is `NOTSET`, it inherits from its parent.

Example:

```python
api.setLevel(NOTSET)
users.setLevel(NOTSET)
```

Both inherit level 20 from `myapp`.

---

## Level Inheritance  
Level inheritance follows these rules:

- If a logger’s level is NOTSET → inherit from parent  
- If a logger has an explicit level → use that level  
- If no parent has an explicit level → default to INFO  

Example:

```python
root = SmartLogger("myapp", level=30)  # INFO
api = SmartLogger("myapp.api")         # inherits INFO
users = SmartLogger("myapp.api.users", level=10)  # DEBUG
```

`users` logs DEBUG and above, while `api` logs INFO and above.

---

## Handler Behavior  
LogSmith’s handler model is intentionally simple:

- **Handlers do NOT propagate upward**  
- **Each logger manages its own handlers**  
- **Console handlers are limited to one per logger**  
- **File handlers can be many per logger**  

This avoids the classic “logger soup” problem where multiple handlers accidentally duplicate output.

Example:

```python
root.add_console()
api.add_file(log_dir="logs", logfile_name="api.log")
users.add_file(log_dir="logs", logfile_name="users.log")
```

Each logger writes only to its own handlers.

---

## Propagation and Auditing  
Propagation is disabled by default.

It is only enabled when auditing is turned on:

```python
SmartLogger.audit_everything(log_dir="audit", logfile_name="audit.log")
```

When auditing is active:

- all loggers propagate upward  
- the audit handler receives all events  
- individual handlers still work normally  

This gives you a global audit trail without interfering with normal logging.

---

## Logger Discovery  
You can retrieve existing loggers:

```python
logger = SmartLogger.get_logger("myapp.api.users")
```

If the logger does not exist, it is created automatically.

---

## Replacing or Resetting Loggers  
Loggers can be:

### Retired  
Handlers are closed and the logger is disabled:

```python
logger.retire()
```

### Destroyed  
Removed entirely from the logging system:

```python
logger.destroy()
```

This allows clean recreation:

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
api.add_file(log_dir="logs", logfile_name="api.log")

users = SmartLogger("myapp.api.users")
users.add_file(log_dir="logs", logfile_name="users.log")
```

---

## Hierarchy in AsyncSmartLogger  
AsyncSmartLogger uses the same hierarchy rules:

```python
root = AsyncSmartLogger("service")
api = AsyncSmartLogger("service.api")
users = AsyncSmartLogger("service.api.users")
```

Async logging methods (`a_info`, `a_error`, etc.) work identically across the hierarchy.

Auditing also works the same way, with async‑aware propagation.

---

## Best Practices  
- Use dot‑separated names to organize modules.  
- Set levels at higher nodes; inherit downward.  
- Attach console handlers only to the root logger.  
- Attach file handlers to specific modules.  
- Use auditing for global capture.  
- Avoid attaching many handlers to many loggers — keep it clean.  

---

## Summary  
Logger hierarchy in LogSmith provides:

- predictable parent–child relationships  
- clean level inheritance  
- non‑propagating handlers  
- optional global auditing  
- easy organization for large applications  
- identical behavior for sync and async loggers  
- safe retirement and recreation of loggers  

The next chapter covers **Lifecycle Management** — how loggers are created, retired, destroyed, and safely shut down.
