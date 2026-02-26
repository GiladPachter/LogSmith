# 🌳 Logger Hierarchy

SmartLogger follows the same hierarchical naming model as Python’s built‑in logging system, but with **cleaner behavior**:<br/>
- **no accidental handler inheritance**
- **predictable propagation rules**.

Logger names define a hierarchy tree structure:

```
myapp
myapp.api
myapp.api.users
```

---

## 🔹 Creating Loggers in a Hierarchy

```python
root_logger   = SmartLogger("myapp")
api_logger    = SmartLogger("myapp.api")
users_logger  = SmartLogger("myapp.api.users")
```

Each logger is independent unless you explicitly enable propagation.</br>
**Note:** a root logger may not be named "root". it is reserved for internal SmartLogger logic.

---

# 🔹 Handler Inheritance

SmartLogger **does not** inherit handlers from parent loggers.
- No accidental duplication
- No unexpected handler chains
- No “double logging”
- Each logger is explicit and predictable

---

# 🔹 Propagation Behavior

By default:

- `propagate = False` for all SmartLogger instances
- Logs stay local to the logger

Propagation is automatically enabled only when **auditing** is active.

---

## 🔹 Propagation Enabled (Auditing Mode)

```python
SmartLogger.audit_everything(...)
```

This:
- attaches an audit handler to the root logger
- sets `propagate = True` on all SmartLogger instances
- duplicates all logs into the audit file

---

# 🔹 Level Inheritance

- If a logger’s level is **NOTSET**, it inherits its level from its parent
- If a logger has an explicit level, it uses that level, which renders the semantic inheritance meaningless.

Example:
```python
root = SmartLogger("myapp", level = levels["INFO"])
child = SmartLogger("myapp.api")  # NOTSET → inherits INFO
```

---

# 🔹 Independent Handlers

```python
api = SmartLogger("myapp.api")
api.add_console()

users = SmartLogger("myapp.api.users")
users.add_file(log_dir="logs", logfile_name="users.log")
```

Result:

- `api` logs to console
- `users` logs to file
- No cross‑contamination

---

# 🔹 Retiring or Destroying Loggers
```python
logger.retire()   # closes handlers
logger.destroy()  # removes logger entirely
```

---

# 🧩 Summary

LogSmith’s hierarchy system provides:
- predictable parent/child relationships
- no accidental handler inheritance
- explicit handler management
- clean propagation rules
- level inheritance only when desired
- safe logger lifecycle management
